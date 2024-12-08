"""Base classes and utilities for violation tab implementations.

This module provides the foundation for all violation-specific tabs,
including common filtering, display, and data management functionality
that is shared across different violation type views.
"""

from abc import (
    ABC,
    ABCMeta,
    abstractmethod,
)

import pandas as pd
from PyQt5.QtCore import (
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from table_utils import setup_table_copy_functionality
from violation_model import ViolationModel


class BaseViolationColumns:
    """Shared column configurations for violation tabs."""

    COMMON_COLUMNS = [
        "carrier_name",
        "list_status",
        "date",
        "total_hours",
        "remedy_total",
    ]

    ROUTE_SPECIFIC_COLUMNS = [
        "own_route_hours",
        "off_route_hours",
        "moves",
    ]

    @classmethod
    def get_columns(cls, include_route_data=False, include_violation_type=False):
        """Get column list with optional additions."""
        columns = cls.COMMON_COLUMNS.copy()
        if include_route_data:
            columns.extend(cls.ROUTE_SPECIFIC_COLUMNS)
        if include_violation_type:
            columns.append("violation_type")
        return columns


class TabRefreshMixin:
    """Mixin providing common tab refresh functionality."""

    def refresh_tabs(self, data=None):
        """Common tab refresh logic."""
        if data is None or data.empty:
            self.init_no_data_tab()
            return

        current_tab = self.get_current_tab_info()
        self.clear_all_tabs()
        return current_tab

    def get_current_tab_info(self):
        """Get current tab index and name."""
        index = self.date_tabs.currentIndex()
        return {"index": index, "name": self.date_tabs.tabText(index)}

    def clear_all_tabs(self):
        """Clear all tabs and reset state."""
        while self.date_tabs.count():
            self.date_tabs.removeTab(0)
        self.models.clear()
        self.showing_no_data = False


class ViolationFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering violation data with multiple filter types."""

    def __init__(self):
        """Initialize the filter proxy model."""
        super().__init__()
        self.filter_text = ""
        self.filter_type = "name"

    def set_filter(self, text, filter_type="name"):
        """Set both the filter text and type.

        Args:
            text (str): Text to filter by
            filter_type (str): Type of filter to apply ('name', 'list_status', or 'violations')
        """
        self.filter_type = filter_type
        self.filter_text = text.lower() if text else ""
        self.invalidateFilter()

    def filter_accepts_row(self, source_row, source_parent):
        """Apply the current filter to determine row visibility.

        Args:
            source_row (int): Row index in the source model
            source_parent (QModelIndex): Parent index in source model

        Returns:
            bool: True if row should be shown, False if filtered out
        """
        source_model = self.sourceModel()

        if not self.filter_text and self.filter_type != "violations":
            return True

        if self.filter_type == "list_status":
            list_status_col = None
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() in ["list_status", "list status"]:
                    list_status_col = col
                    break

            if list_status_col is not None:
                idx = source_model.index(source_row, list_status_col, source_parent)
                list_status = source_model.data(idx, Qt.DisplayRole)
                if list_status:
                    return str(list_status).lower() == self.filter_text.lower()
            return False

        if self.filter_type == "name":
            name_col = None
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() in ["carrier_name", "carrier name"]:
                    name_col = col
                    break

            if name_col is not None:
                idx = source_model.index(source_row, name_col, source_parent)
                name = source_model.data(idx, Qt.DisplayRole)
                if name:
                    return self.filter_text.lower() in str(name).lower()
            return False

        if self.filter_type == "violations":
            # First check for remedy total columns
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if header and any(
                    x in str(header).lower()
                    for x in ["remedy total", "weekly remedy total"]
                ):
                    idx = source_model.index(source_row, col, source_parent)
                    value = source_model.data(idx, Qt.DisplayRole)
                    try:
                        if float(str(value).split()[0]) > 0:
                            return True
                    except (ValueError, TypeError, IndexError):
                        continue

            # Then check for violation type columns
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if header and any(
                    x in str(header).lower()
                    for x in ["violation type", "violation_type"]
                ):
                    idx = source_model.index(source_row, col, source_parent)
                    value = source_model.data(idx, Qt.DisplayRole)
                    if value and not str(value).lower().startswith("no violation"):
                        return True

            # If we get here and haven't found any violations, filter out the row
            return False

        return True

    def filter_accepts_column(self, source_column, source_parent):
        """Accept all columns by default."""
        return True

    # Override Qt method names to maintain compatibility
    filterAcceptsRow = filter_accepts_row
    filterAcceptsColumn = filter_accepts_column


# Create a metaclass that combines QWidget and ABC
class MetaQWidgetABC(type(QWidget), ABCMeta):
    """Metaclass combining QWidget and ABC metaclasses."""

    pass


class BaseViolationTab(QWidget, ABC, TabRefreshMixin, metaclass=MetaQWidgetABC):
    """Base class for all violation tab implementations."""

    data_refreshed = pyqtSignal(pd.DataFrame)

    def __init__(self, parent=None, otdl_enabled=False):
        """Initialize the base violation tab.

        Args:
            parent: Parent widget
            otdl_enabled: Whether OTDL functionality is enabled
        """
        super().__init__(parent)
        self.otdl_enabled = otdl_enabled
        self.models = {}
        self.proxy_models = set()
        self.showing_no_data = True
        self.summary_proxy_model = None
        self.current_filter = ""
        self.current_filter_type = "name"
        self.tab_type = None  # Will be set by subclasses

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        self.main_layout = QVBoxLayout(self)

        # Create search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter carriers...")
        self.search_box.textChanged.connect(self.filter_carriers)
        self.main_layout.addWidget(self.search_box)

        # Create tab widget
        self.date_tabs = QTabWidget()
        self.main_layout.addWidget(self.date_tabs)

        # Create filter buttons
        self._create_filter_buttons()

        # Connect tab change signal
        self.date_tabs.currentChanged.connect(self.update_stats)
        self.date_tabs.currentChanged.connect(self.maintain_current_filter)

        # Initialize with no data
        self.init_no_data_tab()

    def _create_filter_buttons(self):
        """Create and set up filter buttons."""
        self.stats_layout = QHBoxLayout()

        self.total_btn = self.create_filter_button("Total Carriers")
        self.wal_btn = self.create_filter_button("WAL")
        self.nl_btn = self.create_filter_button("NL")
        self.otdl_btn = self.create_filter_button("OTDL")
        self.ptf_btn = self.create_filter_button("PTF")
        self.violations_btn = self.create_filter_button("Carriers With Violations")

        for btn in [
            self.total_btn,
            self.wal_btn,
            self.nl_btn,
            self.otdl_btn,
            self.ptf_btn,
            self.violations_btn,
        ]:
            self.stats_layout.addWidget(btn)

        self.stats_layout.addStretch()
        self.main_layout.addLayout(self.stats_layout)

    @abstractmethod
    def get_display_columns(self) -> list:
        """Return list of columns to display for this violation type."""
        pass

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in violation tab."""
        return date_data.copy()

    def configure_tab_view(self, view: QTableView, model: ViolationModel):
        """Configure the tab view after creation."""
        pass

    def create_filter_button(self, text):
        """Create a styled filter button for list status filtering."""
        btn = QPushButton(f"{text}: 0")
        btn.setCheckable(True)
        btn.clicked.connect(self.handle_filter_click)
        return btn

    def handle_filter_click(self):
        """Handle clicks on filter buttons."""
        sender = self.sender()

        # Uncheck other buttons
        for btn in [
            self.total_btn,
            self.wal_btn,
            self.nl_btn,
            self.otdl_btn,
            self.ptf_btn,
            self.violations_btn,
        ]:
            if btn != sender:
                btn.setChecked(False)

        if not sender.isChecked():
            self.filter_carriers("")
            return

        # Apply appropriate filter
        if sender == self.total_btn:
            self.filter_carriers("")
        elif sender == self.wal_btn:
            self.filter_carriers("wal", filter_type="list_status")
        elif sender == self.nl_btn:
            self.filter_carriers("nl", filter_type="list_status")
        elif sender == self.otdl_btn:
            self.filter_carriers("otdl", filter_type="list_status")
        elif sender == self.ptf_btn:
            self.filter_carriers("ptf", filter_type="list_status")
        elif sender == self.violations_btn:
            self.filter_carriers("", filter_type="violations")

    def filter_carriers(self, text, filter_type="name"):
        """Filter carriers across all tabs based on search criteria."""
        if self.showing_no_data:
            return

        self.current_filter = text
        self.current_filter_type = filter_type

        current_tab_index = self.date_tabs.currentIndex()
        if current_tab_index == -1:
            return

        current_tab_name = self.date_tabs.tabText(current_tab_index)

        try:
            proxy_model = (
                self.summary_proxy_model
                if current_tab_name == "Summary"
                else self.models[current_tab_name]["proxy"]
            )
            proxy_model.set_filter(text, filter_type)
            self.update_stats()
        except Exception as e:
            print(f"Error filtering carriers: {str(e)}")

    def update_stats(self):
        """Update statistics and button texts."""
        if self.showing_no_data:
            self.reset_button_counts()
            return

        current_tab_index = self.date_tabs.currentIndex()
        if current_tab_index == -1:
            return

        try:
            current_tab_name = self.date_tabs.tabText(current_tab_index)
            df = (
                self.summary_proxy_model.sourceModel().df
                if current_tab_name == "Summary"
                else self.models[current_tab_name]["model"].df
            )

            total_carriers = len(df)
            list_status_col = (
                "list_status" if "list_status" in df.columns else "List Status"
            )

            if list_status_col in df.columns:
                wal_carriers = len(df[df[list_status_col].str.lower() == "wal"])
                nl_carriers = len(df[df[list_status_col].str.lower() == "nl"])
                otdl_carriers = len(df[df[list_status_col].str.lower() == "otdl"])
                ptf_carriers = len(df[df[list_status_col].str.lower() == "ptf"])
            else:
                wal_carriers = nl_carriers = otdl_carriers = ptf_carriers = 0

            violations = self._calculate_violations(df)

            self.total_btn.setText(f"Total Carriers: {total_carriers}")
            self.wal_btn.setText(f"WAL: {wal_carriers}")
            self.nl_btn.setText(f"NL: {nl_carriers}")
            self.otdl_btn.setText(f"OTDL: {otdl_carriers}")
            self.ptf_btn.setText(f"PTF: {ptf_carriers}")
            self.violations_btn.setText(f"Carriers With Violations: {violations}")

        except Exception as e:
            print(f"Error updating stats: {str(e)}")
            self.reset_button_counts()

    def _calculate_violations(self, df):
        """Calculate the total number of violations in the given data."""
        for col in ["Weekly Remedy Total", "Remedy Total", "remedy_total", "total"]:
            if col in df.columns:
                return len(df[df[col] > 0])
        return 0

    def reset_button_counts(self):
        """Reset all button counts to zero."""
        self.total_btn.setText("Total Carriers: 0")
        self.wal_btn.setText("WAL: 0")
        self.nl_btn.setText("NL: 0")
        self.otdl_btn.setText("OTDL: 0")
        self.ptf_btn.setText("PTF: 0")
        self.violations_btn.setText("Carriers With Violations: 0")

    def init_no_data_tab(self):
        """Initialize the No Data tab."""
        self.date_tabs.clear()
        no_data_view = QTableView()
        no_data_view.setModel(None)
        self.date_tabs.addTab(no_data_view, "No Data")

    def create_table_view(self, model, proxy_model=None):
        """Create and configure a table view for violation data."""
        view = QTableView()

        if isinstance(model, ViolationModel):
            renamed_df = self._rename_columns(model.df)
            model.df = renamed_df
            model.layoutChanged.emit()

        view.setModel(proxy_model if proxy_model else model)
        view.setSortingEnabled(True)
        setup_table_copy_functionality(view)

        if proxy_model:
            proxy_model.sort(0, Qt.AscendingOrder)

        view.resizeColumnsToContents()
        return view

    def _rename_columns(self, df):
        """Rename DataFrame columns to user-friendly display names."""
        df = df.copy()
        rename_map = {
            "carrier_name": "Carrier Name",
            "list_status": "List Status",
            "date": "Date",
            "daily_hours": "Daily Hours",
            "total_hours": "Total Hours",
            "remedy_total": "Remedy Total",
            "violation_type": "Violation Type",
            "cumulative_hours": "Cumulative Hours",
            "own_route_hours": "Own Route Hours",
            "off_route_hours": "Off Route Hours",
            "moves": "Moves",
        }
        existing_columns = {
            col: new_name for col, new_name in rename_map.items() if col in df.columns
        }
        if existing_columns:
            df.rename(columns=existing_columns, inplace=True)
        return df

    def maintain_current_filter(self, index):
        """Maintain active filters when switching between tabs."""
        if self.current_filter or self.current_filter_type != "name":
            self.filter_carriers(self.current_filter, self.current_filter_type)
        self._resize_columns_on_current_tab(index)

    def _resize_columns_on_current_tab(self, index):
        """Resize columns to fit their contents on the current tab."""
        current_widget = self.date_tabs.widget(index)
        if isinstance(current_widget, QTableView):
            current_widget.resizeColumnsToContents()

    def init_ui(self, initial_data=None):
        """Initialize the UI with optional initial data.

        This method is kept for backwards compatibility with main_gui.py.

        Args:
            initial_data: Optional DataFrame to initialize the view with
        """
        if initial_data is not None and not initial_data.empty:
            self.refresh_data(initial_data)

    # Alias for backwards compatibility
    initUI = init_ui

    def refresh_data(self, violation_data):
        """Refresh the tab with new violation data."""
        if violation_data.empty:
            self.init_no_data_tab()
            return

        current_tab = self.get_current_tab_info()
        self.clear_all_tabs()

        date_column = "rings_date" if "rings_date" in violation_data.columns else "date"

        # Create tabs for each date
        for date in sorted(violation_data[date_column].unique()):
            date_data = violation_data[violation_data[date_column] == date]
            self.create_tab_for_date(date, date_data)

        # Add summary tab
        self.add_summary_tab(violation_data)

        # Restore tab selection
        self.restore_tab_selection(current_tab["name"])

    def restore_tab_selection(self, current_tab_name):
        """Restore the previously selected tab."""
        if current_tab_name == "Summary":
            self.date_tabs.setCurrentIndex(self.date_tabs.count() - 1)
        else:
            for i in range(self.date_tabs.count()):
                if self.date_tabs.tabText(i) == current_tab_name:
                    self.date_tabs.setCurrentIndex(i)
                    break

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing violations for a specific date."""
        display_columns = self.get_display_columns()
        formatted_data = self.format_display_data(date_data)

        if display_columns:
            formatted_data = formatted_data[display_columns]

        model = ViolationModel(formatted_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}
        self.date_tabs.addTab(view, str(date))
        self.configure_tab_view(view, model)

        return view

    def add_summary_tab(self, data):
        """Create or update the summary tab with weekly violation totals."""
        carrier_status = data.groupby("carrier_name")["list_status"].first()
        value_column = "total" if "total" in data.columns else "remedy_total"
        date_column = "rings_date" if "rings_date" in data.columns else "date"

        daily_totals = data.pivot_table(
            index="carrier_name",
            columns=date_column,
            values=value_column,
            aggfunc="sum",
            fill_value=0,
        )

        weekly_totals = data.groupby("carrier_name")[value_column].sum()

        summary_data = pd.concat(
            [
                carrier_status.rename("list_status"),
                weekly_totals.rename("Weekly Remedy Total"),
                daily_totals,
            ],
            axis=1,
        ).reset_index()

        # Reorder columns to put list_status after carrier_name
        columns = summary_data.columns.tolist()
        columns.remove("list_status")
        columns.insert(1, "list_status")
        summary_data = summary_data[columns]

        # Round numerical columns
        for col in summary_data.columns:
            if col not in ["carrier_name", "list_status"]:
                summary_data[col] = summary_data[col].round(2)

        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.summary_proxy_model = proxy_model
        self.date_tabs.addTab(view, "Summary")

    def create_summary_model(self, summary_data: pd.DataFrame):
        """Create a model for the summary tab.

        Args:
            summary_data: Processed data for the summary view

        Returns:
            tuple: (model, view) The configured model and view
        """
        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.summary_proxy_model = proxy_model
        return model, view

    def create_summary_proxy_model(self, model):
        """Create a proxy model for the summary tab's data.

        Args:
            model: Source model containing summary data

        Returns:
            ViolationFilterProxyModel: Configured proxy model for filtering
        """
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        return proxy_model

    def register_proxy_model(self, proxy_model):
        """Register a new proxy model for filtering."""
        self.proxy_models.add(proxy_model)
        if self.current_filter or self.current_filter_type != "name":
            proxy_model.set_filter(self.current_filter, self.current_filter_type)

    def create_violation_model(self, data, proxy=True):
        """Create a model for the violation data.

        Args:
            data: The data to model
            proxy: Whether to create a proxy model

        Returns:
            tuple: (model, proxy_model) or (model, None)
        """
        model = ViolationModel(data, tab_type=self.tab_type)

        if proxy:
            proxy_model = ViolationFilterProxyModel()
            proxy_model.setSourceModel(model)
            return model, proxy_model
        return model, None
