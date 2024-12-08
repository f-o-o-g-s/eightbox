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
from violation_types import ViolationType


class SummaryProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering summary data in violation tabs.

    Provides case-insensitive filtering of carrier names in summary views.
    Maintains a single filter string that is applied across all rows.
    """

    def __init__(self):
        super().__init__()
        self._filter_text = ""

    def setFilterFixedString(self, text):
        """Set the filter string for carrier name filtering.

        Args:
            text (str): Text to filter by (case-insensitive)
        """
        self._filter_text = text.lower()
        super().setFilterFixedString(text)

    def filterAcceptsRow(self, source_row, source_parent):
        """Determine if a row should be shown based on the current filter.

        Args:
            source_row (int): Row index in the source model
            source_parent (QModelIndex): Parent index in source model

        Returns:
            bool: True if row should be shown, False if filtered out
        """
        model = self.sourceModel()
        carrier_idx = model.index(source_row, 0, source_parent)
        carrier_name = str(model.data(carrier_idx, Qt.DisplayRole)).lower()

        if not self._filter_text:
            return True

        return self._filter_text in carrier_name


class ViolationFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering violation data with multiple filter types.

    Supports filtering by:
    - Carrier name (case-insensitive substring match)
    - List status (exact match)
    - Violation status

    The filter type can be changed dynamically while maintaining the current
    filter text.
    """

    def __init__(self):
        """Initialize the filter proxy model."""
        super().__init__()
        self.filter_text = ""
        self.filter_type = "name"

    def set_filter(self, text, filter_type="name"):
        """Set both the filter text and type.

        Args:
            text (str): Text to filter by
            filter_type (str): Type of filter to apply ('name' or 'list_status')
        """
        self.filter_type = filter_type
        self.filter_text = text.lower() if text else ""
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Apply the current filter to determine row visibility.

        Handles different filter types:
        - name: Case-insensitive substring match on carrier name
        - list_status: Exact match on carrier's list status
        - violations: Show only carriers with violations

        Args:
            source_row (int): Row index in the source model
            source_parent (QModelIndex): Parent index in source model

        Returns:
            bool: True if row should be shown, False if filtered out
        """
        source_model = self.sourceModel()

        # If no filter text, show all rows
        if not self.filter_text:
            return True

        if self.filter_type == "list_status":
            # Get list_status value
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() == "list_status":
                    idx = source_model.index(source_row, col, source_parent)
                    list_status = source_model.data(idx, Qt.DisplayRole)
                    if list_status:
                        return str(list_status).lower() == self.filter_text

        elif self.filter_type == "name":
            # Original name filtering
            idx = source_model.index(source_row, 0, source_parent)
            name = source_model.data(idx, Qt.DisplayRole)
            if name:
                return self.filter_text in str(name).lower()

        return True

    def filterAcceptsColumn(self, source_column, source_parent):
        """Accept all columns by default."""
        return True


# Create a metaclass that combines QWidget and ABC
class MetaQWidgetABC(type(QWidget), ABCMeta):  # type: ignore[misc]
    """Metaclass combining QWidget and ABC metaclasses.

    This metaclass allows the BaseViolationTab to properly inherit from both
    QWidget and ABC, enabling both Qt widget functionality and abstract method
    definition in a single class.

    Note:
        Required to resolve metaclass conflict between QWidget and ABC
        when creating abstract base classes that are also Qt widgets.
    """

    pass


class BaseViolationTab(QWidget, ABC, metaclass=MetaQWidgetABC):
    """Base class for all violation tab implementations.

    Provides core functionality for displaying and managing violation data including:
    - Filtering and sorting capabilities
    - Date-based tab management
    - Statistics tracking and display
    - List status filtering buttons
    - Common table view setup

    Attributes:
        data_refreshed (pyqtSignal): Signal emitted when data is updated
        otdl_enabled (bool): Whether OTDL functionality is enabled
        tab_type (ViolationType): Type of violation this tab handles
        models (dict): Maps dates to their corresponding models and views
        showing_no_data (bool): Whether the tab is showing the no-data state
    """

    data_refreshed = pyqtSignal(pd.DataFrame)

    def __init__(self, parent=None, otdl_enabled=False, tab_type: ViolationType = None):
        super().__init__(parent)
        self.otdl_enabled = otdl_enabled
        self.tab_type = tab_type
        self.models = {}
        self.proxy_models = {}
        self.showing_no_data = True

        # Create the main layout
        self.main_layout = QVBoxLayout(self)

        # Create single search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter carriers...")
        self.search_box.textChanged.connect(self.filter_carriers)
        self.main_layout.addWidget(self.search_box)

        # Create tab widget
        self.date_tabs = QTabWidget()
        self.main_layout.addWidget(self.date_tabs)

        # Create the stats display as a horizontal layout with filter buttons
        self.stats_layout = QHBoxLayout()

        # Create filter buttons
        self.total_btn = self.create_filter_button("Total Carriers")
        self.wal_btn = self.create_filter_button("WAL")
        self.nl_btn = self.create_filter_button("NL")
        self.otdl_btn = self.create_filter_button("OTDL")
        self.ptf_btn = self.create_filter_button("PTF")
        self.violations_btn = self.create_filter_button("Carriers With Violations")

        # Add buttons to layout
        self.stats_layout.addWidget(self.total_btn)
        self.stats_layout.addWidget(self.wal_btn)
        self.stats_layout.addWidget(self.nl_btn)
        self.stats_layout.addWidget(self.otdl_btn)
        self.stats_layout.addWidget(self.ptf_btn)
        self.stats_layout.addWidget(self.violations_btn)
        self.stats_layout.addStretch()

        # Replace stats label with new layout
        self.main_layout.addLayout(self.stats_layout)

        # Connect tab change signal to update stats
        self.date_tabs.currentChanged.connect(self.update_stats)

        # Initialize with no data
        self.init_no_data_tab()

        # Add filter state tracking
        self.current_filter = ""
        self.current_filter_type = "name"

        # Connect tab change signal to maintain filters
        self.date_tabs.currentChanged.connect(self.maintain_current_filter)

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

            # Update button texts with counts
            total_carriers = len(df)

            # Check both original and renamed column names for list_status
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

            violations = self.calculate_violations(df)

            self.total_btn.setText(f"Total Carriers: {total_carriers}")
            self.wal_btn.setText(f"WAL: {wal_carriers}")
            self.nl_btn.setText(f"NL: {nl_carriers}")
            self.otdl_btn.setText(f"OTDL: {otdl_carriers}")
            self.ptf_btn.setText(f"PTF: {ptf_carriers}")
            self.violations_btn.setText(f"Carriers With Violations: {violations}")

        except Exception as e:
            print(f"Error updating stats: {str(e)}")
            self.reset_button_counts()

    def reset_button_counts(self):
        """Reset all button counts to zero."""
        self.total_btn.setText("Total Carriers: 0")
        self.wal_btn.setText("WAL: 0")
        self.nl_btn.setText("NL: 0")
        self.otdl_btn.setText("OTDL: 0")
        self.ptf_btn.setText("PTF: 0")
        self.violations_btn.setText("Carriers With Violations: 0")

    def initUI(self, initial_data=None):
        """Initialize the UI with optional initial data."""
        if initial_data is not None and not initial_data.empty:
            self.refresh_data(initial_data)

    def init_no_data_tab(self):
        """Initialize the No Data tab"""
        self.date_tabs.clear()
        no_data_view = QTableView()
        no_data_view.setModel(None)
        self.date_tabs.addTab(no_data_view, "No Data")

    def filter_carriers(self, text, filter_type="name"):
        """Filter carriers across all tabs based on search criteria.

        Applies the filter to both regular date tabs and the summary tab.
        Updates statistics after filtering.

        Args:
            text (str): Text to filter by
            filter_type (str): Type of filter to apply ('name', 'list_status', 'violations')
        """
        if self.showing_no_data:
            return

        # Store current filter state
        self.current_filter = text
        self.current_filter_type = filter_type

        current_tab_index = self.date_tabs.currentIndex()
        if current_tab_index == -1:
            return

        current_tab_name = self.date_tabs.tabText(current_tab_index)

        try:
            # Get the appropriate proxy model
            if current_tab_name == "Summary":
                proxy_model = self.summary_proxy_model
            else:
                proxy_model = self.models[current_tab_name]["proxy"]

            # Apply the filter
            proxy_model.set_filter(text, filter_type)

            # Update stats after filtering
            self.update_stats()
        except Exception as e:
            print(f"Error filtering carriers: {str(e)}")

    def calculate_violations(self, df):
        """Calculate the total number of violations in the given data.

        Handles multiple possible column names for remedy totals to support
        different violation types.

        Args:
            df (pd.DataFrame): Violation data to analyze

        Returns:
            int: Number of carriers with violations
        """
        # Check both original and renamed column names
        if "Weekly Remedy Total" in df.columns:
            return len(df[df["Weekly Remedy Total"] > 0])
        elif "Remedy Total" in df.columns:
            return len(df[df["Remedy Total"] > 0])
        elif "remedy_total" in df.columns:
            return len(df[df["remedy_total"] > 0])
        elif "total" in df.columns:
            return len(df[df["total"] > 0])
        return 0

    def register_proxy_model(self, proxy_model):
        """Register a new proxy model for filtering."""
        self.proxy_models.add(proxy_model)
        self._apply_filter_to_model(proxy_model)

    def create_violation_model(self, data, proxy=True, proxy_class=None):
        """Create a model for the violation data."""
        print(
            f"Creating violation model with args: "
            f"data={type(data)}, proxy={proxy}, proxy_class={proxy_class}"
        )
        model = ViolationModel(data)

        if proxy:
            # Use our custom proxy model by default
            proxy_model = ViolationFilterProxyModel()
            proxy_model.setSourceModel(model)
            return model, proxy_model
        return model, None

    def create_table_view(self, model, proxy_model=None):
        """Create and configure a table view for violation data.

        Sets up:
        - Sorting capability
        - Copy functionality
        - Column sizing
        - Model/proxy model connections

        Args:
            model (ViolationModel): The source model containing violation data
            proxy_model (QSortFilterProxyModel, optional): Proxy model for filtering

        Returns:
            QTableView: Configured table view
        """
        view = QTableView()

        # Rename columns before setting the model
        if isinstance(model, ViolationModel):
            # Update the model's dataframe with renamed columns
            renamed_df = self.rename_columns(model.df)
            model.df = renamed_df
            model.layoutChanged.emit()  # Notify the view of the changes

        view.setModel(proxy_model if proxy_model else model)
        view.setSortingEnabled(True)
        setup_table_copy_functionality(view)

        if proxy_model:
            proxy_model.sort(0, Qt.AscendingOrder)

        # Resize columns to content
        view.resizeColumnsToContents()

        return view

    def rename_columns(self, df):
        """Rename DataFrame columns to user-friendly display names.

        Maintains consistent column naming across all violation types.
        Only renames columns that exist in the input DataFrame.

        Args:
            df (pd.DataFrame): DataFrame with original column names

        Returns:
            pd.DataFrame: DataFrame with renamed columns
        """
        # Create a copy of the dataframe to avoid the SettingWithCopyWarning
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

        # Only rename columns that exist in the dataframe
        existing_columns = {
            col: new_name for col, new_name in rename_map.items() if col in df.columns
        }
        if existing_columns:
            df.rename(columns=existing_columns, inplace=True)

        return df

    def create_tab_for_date(self, date, date_data):
        """Create a new tab for a specific date's violation data.

        Sets up:
        - Data model and proxy model
        - Table view with proper configuration
        - Tab registration in the tab widget

        Args:
            date (datetime.date): Date for the new tab
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab
        """
        model, proxy_model = self.create_violation_model(
            date_data, proxy=True, tab_type=self.tab_type
        )
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}
        self.proxy_models[str(date)] = proxy_model

        self.date_tabs.addTab(view, str(date))
        return view

    def create_summary_proxy_model(self, model):
        """Create a proxy model for the summary tab's data.

        Args:
            model (ViolationModel): Source model containing summary data

        Returns:
            ViolationFilterProxyModel: Configured proxy model for filtering
        """
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        return proxy_model

    def resize_columns_on_current_tab(self, index):
        """Resize columns to fit their contents on the current tab.

        Args:
            index (int): Index of the current tab
        """
        current_widget = self.date_tabs.widget(index)
        if isinstance(current_widget, QTableView):
            current_widget.resizeColumnsToContents()

    @abstractmethod
    def refresh_data(self, violation_data):
        """Refresh the tab's data with new violation information.

        Must be implemented by subclasses to handle specific violation types.
        Should clear existing tabs and create new ones based on the data.

        Args:
            violation_data (pd.DataFrame): New violation data to display
        """
        pass

    @abstractmethod
    def add_summary_tab(self, data):
        """Add or update the summary tab with aggregated violation data.

        Must be implemented by subclasses to handle specific violation types.
        Should create a summary view of all violations across dates.

        Args:
            data (pd.DataFrame): Aggregated data for summary display
        """
        pass

    def create_filter_button(self, text):
        """Create a styled filter button for list status filtering.

        Creates a checkable button with:
        - Initial count of 0
        - Connected click handler
        - Consistent styling

        Args:
            text (str): Button label (e.g., "WAL", "NL", "OTDL")

        Returns:
            QPushButton: Configured filter button
        """
        btn = QPushButton(f"{text}: 0")
        btn.setCheckable(True)
        btn.clicked.connect(self.handle_filter_click)
        return btn

    def handle_filter_click(self):
        """Handle clicks on filter buttons (WAL, NL, OTDL, etc.).

        Manages button states and applies appropriate filters:
        - Unchecks other buttons when one is selected
        - Clears filters when button is unchecked
        - Applies specific list status filters
        - Updates carrier counts and statistics
        """
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

    def apply_list_status_filter(self, status):
        """Apply a filter to show only carriers with specific list status.

        Handles filtering in both regular and summary tabs using the
        appropriate proxy model.

        Args:
            status (str): List status to filter by ("WAL", "NL", "OTDL", "PTF")
        """
        current_tab_index = self.date_tabs.currentIndex()
        if current_tab_index == -1 or self.showing_no_data:
            return

        current_tab_name = self.date_tabs.tabText(current_tab_index)
        proxy_model = (
            self.summary_proxy_model
            if current_tab_name == "Summary"
            else self.models[current_tab_name]["proxy"]
        )

        proxy_model.setFilterRole(Qt.UserRole)  # Use custom role for filtering
        proxy_model.setFilterFixedString(status)

    def apply_violations_filter(self):
        """Apply a filter to show only carriers with violations.

        Uses a custom role in the proxy model to filter based on
        the presence of violations (remedy hours > 0).
        """
        current_tab_index = self.date_tabs.currentIndex()
        if current_tab_index == -1 or self.showing_no_data:
            return

        current_tab_name = self.date_tabs.tabText(current_tab_index)
        proxy_model = (
            self.summary_proxy_model
            if current_tab_name == "Summary"
            else self.models[current_tab_name]["proxy"]
        )

        proxy_model.setFilterRole(Qt.UserRole + 1)  # Use different role for violations
        proxy_model.setFilterFixedString("has_violation")

    def maintain_current_filter(self, index):
        """Maintain active filters when switching between tabs.

        Ensures that the current filter remains applied when:
        - Switching between date tabs
        - Switching to/from summary tab
        - Resizing columns for visibility

        Args:
            index (int): Index of the newly selected tab
        """
        if self.current_filter or self.current_filter_type != "name":
            self.filter_carriers(self.current_filter, self.current_filter_type)
        self.resize_columns_on_current_tab(index)

    def update_table_style(self):
        """Update the table's visual style to match the application theme.

        Applies consistent Material Design styling to:
        - Table background and alternating rows
        - Grid lines and borders
        - Selection highlighting
        - Header sections
        - Hover states
        """
        style = """
            QTableView {
                background-color: #1E1E1E;
                alternate-background-color: #262626;
                gridline-color: #404040;
                color: #E1E1E1;
                selection-background-color: #BB86FC;
                selection-color: #000000;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E1E1E1;
                padding: 5px;
                border: 1px solid #404040;
            }
            QTableView::item:hover {
                background-color: #383838;
            }
        """
        self.view.setStyleSheet(style)
