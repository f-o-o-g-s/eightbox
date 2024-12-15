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
    QLabel,
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

        self.get_current_tab_info()
        self.clear_all_tabs()
        return None

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
        self.current_violation_count = 0

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        self.main_layout = QVBoxLayout(self)

        # Create tab widget
        self.date_tabs = QTabWidget()
        self.main_layout.addWidget(self.date_tabs)

        # Connect tab change signal
        self.date_tabs.currentChanged.connect(self.update_stats)
        self.date_tabs.currentChanged.connect(self.maintain_current_filter)

        # Initialize with no data
        self.init_no_data_tab()

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

    def filter_carriers(self, text, filter_type="name"):
        """Filter carriers across all tabs based on search criteria.

        Args:
            text (str): The text to filter by
            filter_type (str): The type of filter to apply ('name' or 'list_status')
        """
        if self.showing_no_data:
            return

        self.current_filter = text
        self.current_filter_type = filter_type

        # Apply filter to all proxy models
        for model_dict in self.models.values():
            if "proxy" in model_dict:
                proxy_model = model_dict["proxy"]
                proxy_model.set_filter(text, filter_type)

        # Apply to summary proxy model if it exists
        if self.summary_proxy_model:
            self.summary_proxy_model.set_filter(text, filter_type)

        self.update_stats()

    def handle_global_filter_click(self, status_type):
        """Handle global filter click from another tab."""
        # Apply the filter
        if status_type == "all":
            self.filter_carriers("")
        elif status_type == "violations":
            self.filter_carriers("", filter_type="violations")
        else:
            self.filter_carriers(status_type, filter_type="list_status")

        # Don't call update_stats() here - let the main window handle that

    def update_stats(self):
        """Update the statistics display in table headers."""
        try:
            if self.showing_no_data:
                self._update_main_window_stats(0, 0, 0, 0, 0, 0)
                return

            current_tab_index = self.date_tabs.currentIndex()
            if current_tab_index == -1:
                self._update_main_window_stats(0, 0, 0, 0, 0, 0)
                return

            current_tab_name = self.date_tabs.tabText(current_tab_index)

            # Get data for current tab
            df = None
            if current_tab_name in self.models:
                proxy_model = self.models[current_tab_name].get("proxy")
                if proxy_model:
                    source_model = proxy_model.sourceModel()
                    if source_model:
                        df = source_model.df

            if df is None or df.empty:
                self._update_main_window_stats(0, 0, 0, 0, 0, 0)
                return

            # Calculate all stats
            total_carriers = len(df)
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )

            if list_status_col:
                wal_carriers = len(df[df[list_status_col].str.lower() == "wal"])
                nl_carriers = len(df[df[list_status_col].str.lower() == "nl"])
                otdl_carriers = len(df[df[list_status_col].str.lower() == "otdl"])
                ptf_carriers = len(df[df[list_status_col].str.lower() == "ptf"])
            else:
                wal_carriers = nl_carriers = otdl_carriers = ptf_carriers = 0

            # Calculate and store violation count
            violations = self._calculate_violation_count(df)

            # Update the table header with violation count
            self.update_violation_header(self.date_tabs, current_tab_index, violations)

            # Update internal stats
            self._update_main_window_stats(
                total_carriers,
                wal_carriers,
                nl_carriers,
                otdl_carriers,
                ptf_carriers,
                violations,
            )

        except Exception as e:
            print(f"Error updating stats: {str(e)}")
            self._update_main_window_stats(0, 0, 0, 0, 0, 0)

    def _calculate_violation_count(self, df):
        """Calculate the number of carriers with violations in the current view."""
        try:
            # For Summary tab, check numeric columns for any non-zero values
            if self.__class__.__name__ == "ViolationRemediesTab":
                numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
                exclude_cols = ["Total Hours", "Own Route Hours", "Off Route Hours"]
                violation_cols = [
                    col for col in numeric_cols if col not in exclude_cols
                ]
                return len(df[df[violation_cols].gt(0).any(axis=1)])

            # For regular violation tabs
            if "violation_type" in df.columns:
                return len(
                    df[~df["violation_type"].str.contains("No Violation", na=False)]
                )

            # If no violation type column, check remedy totals
            for col in ["remedy_total", "Remedy Total", "Weekly Remedy Total"]:
                if col in df.columns:
                    return len(df[pd.to_numeric(df[col], errors="coerce") > 0])

            # Check for highlighted rows (violations) in any numeric columns
            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
            if len(numeric_cols) > 0:
                return len(df[df[numeric_cols].gt(0).any(axis=1)])

            return 0
        except Exception as e:
            print(f"Error calculating violation count: {str(e)}")
            return 0

    def _update_main_window_stats(self, total, wal, nl, otdl, ptf, violations):
        """Update internal stats tracking.

        Args:
            total (int): Total number of carriers
            wal (int): Number of WAL carriers
            nl (int): Number of NL carriers
            otdl (int): Number of OTDL carriers
            ptf (int): Number of PTF carriers
            violations (int): Number of carriers with violations
        """
        # Store stats internally for filtering purposes
        self.current_stats = {
            "total": total,
            "wal": wal,
            "nl": nl,
            "otdl": otdl,
            "ptf": ptf,
            "violations": violations,
        }

        # Call parent's update_filter_stats with empty implementation
        if hasattr(self.parent(), "update_filter_stats"):
            self.parent().update_filter_stats(total, wal, nl, otdl, ptf, violations)

    def init_no_data_tab(self):
        """Initialize the No Data tab."""
        self.date_tabs.clear()
        no_data_view = QTableView()
        no_data_view.setModel(None)
        self.date_tabs.addTab(no_data_view, "No Data")

    def create_table_view(self, model, proxy_model=None):
        """Create and configure a table view for violation data."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        view = QTableView()
        if isinstance(model, ViolationModel):
            renamed_df = self._rename_columns(model.df)
            model.df = renamed_df
            model.layoutChanged.emit()

        # Set up the model and sorting
        if proxy_model:
            view.setModel(proxy_model)
            proxy_model.setDynamicSortFilter(True)
            proxy_model.setSortRole(Qt.UserRole)  # Use UserRole for sorting
        else:
            view.setModel(model)
        
        view.setSortingEnabled(True)
        setup_table_copy_functionality(view)

        # Configure the header for better sorting behavior
        header = view.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        
        # Initial sort on first column
        if proxy_model:
            proxy_model.sort(0, Qt.AscendingOrder)
            header.sortIndicatorChanged.connect(proxy_model.sort)

        layout.addWidget(view)
        return container

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
            "hour_limit": "Hour Limit",
            "trigger_carrier": "Trigger Carrier",
            "trigger_hours": "Trigger Hours",
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

        # Resize columns for the newly selected tab
        current_widget = self.date_tabs.widget(index)
        if isinstance(current_widget, QWidget):
            table_view = current_widget.findChild(QTableView)
            if table_view and table_view.model():
                header = table_view.horizontalHeader()
                for col in range(table_view.model().columnCount()):
                    header.setSectionResizeMode(col, header.ResizeToContents)

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

        self.get_current_tab_info()
        self.clear_all_tabs()

        date_column = "rings_date" if "rings_date" in violation_data.columns else "date"

        # Create tabs for each date
        for date in sorted(violation_data[date_column].unique()):
            date_data = violation_data[violation_data[date_column] == date]
            self.create_tab_for_date(date, date_data)

        # Add summary tab
        self.add_summary_tab(violation_data)

        # Restore tab selection
        self.restore_tab_selection("Summary")

        # After creating/updating all tabs, update the stats
        self.update_stats()

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
        """Create a new tab for the given date with the provided data."""
        # Format data for display
        formatted_data = self.format_display_data(date_data)

        # Get display columns if specified
        display_columns = self.get_display_columns()
        if display_columns:
            formatted_data = formatted_data[display_columns]

        # Create model and view
        model = ViolationModel(formatted_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        # Store models and add tab
        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}
        tab_index = self.date_tabs.addTab(view, str(date))
        self.configure_tab_view(view, model)

        # Calculate violation counts
        total_violations = 0
        wal_violations = 0
        nl_violations = 0
        otdl_violations = 0
        ptf_violations = 0

        # Count violations by list status
        if "list_status" in formatted_data.columns:
            for list_status in ["wal", "nl", "otdl", "ptf"]:
                count = self._calculate_list_status_violation_count(
                    formatted_data, list_status
                )
                if list_status == "wal":
                    wal_violations = count
                elif list_status == "nl":
                    nl_violations = count
                elif list_status == "otdl":
                    otdl_violations = count
                elif list_status == "ptf":
                    ptf_violations = count
                total_violations += count

        # Create header text
        header_text = (
            f"Total Violations: {total_violations} | "
            f"WAL: {wal_violations} | "
            f"NL: {nl_violations} | "
            f"OTDL: {otdl_violations} | "
            f"PTF: {ptf_violations}"
        )

        # Update header
        self.update_violation_header(
            self.date_tabs, tab_index, total_violations, header_text
        )

        return view

    def add_summary_tab(self, data):
        """Create or update the summary tab with weekly violation totals."""
        carrier_status = data.groupby("carrier_name")["list_status"].first()
        date_column = "rings_date" if "rings_date" in data.columns else "date"

        # For MAX60 tab, we need special handling
        if self.__class__.__name__ == "ViolationMax60Tab":
            # Group by carrier to get weekly totals
            weekly_data = (
                data.groupby("carrier_name")
                .agg(
                    {
                        "list_status": "first",
                        "daily_hours": "sum",
                    }
                )
                .reset_index()
            )

            # Calculate weekly remedy total only for eligible carriers who worked over 60 hours
            weekly_data["Weekly Remedy Total"] = weekly_data.apply(
                lambda row: max(0, row["daily_hours"] - 60)
                if (
                    row["list_status"].lower() in ["wal", "nl", "otdl"]
                    and row["daily_hours"] > 60
                )
                else 0,
                axis=1,
            )

            # Get daily totals
            daily_totals = data.pivot_table(
                index="carrier_name",
                columns=date_column,
                values="daily_hours",
                aggfunc="sum",
                fill_value=0,
            )

            summary_data = pd.concat(
                [
                    weekly_data.set_index("carrier_name")[
                        ["list_status", "Weekly Remedy Total"]
                    ],
                    daily_totals,
                ],
                axis=1,
            ).reset_index()

        else:
            # For other violation types, use existing logic
            value_column = "total" if "total" in data.columns else "remedy_total"
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

        # Add violation count header for summary tab
        violations = self._calculate_violation_count(summary_data)
        if "list_status" in summary_data.columns:
            # Calculate violations for each list status using the same logic
            ptf_violations = self._calculate_list_status_violation_count(
                summary_data, "ptf"
            )
            wal_violations = self._calculate_list_status_violation_count(
                summary_data, "wal"
            )
            nl_violations = self._calculate_list_status_violation_count(
                summary_data, "nl"
            )
            otdl_violations = self._calculate_list_status_violation_count(
                summary_data, "otdl"
            )

            header_text = (
                f"Total Violations: {violations}  |  "
                f"WAL: {wal_violations}  |  "
                f"NL: {nl_violations}  |  "
                f"OTDL: {otdl_violations}  |  "
                f"PTF: {ptf_violations}"
            )
            self.update_violation_header(
                self.date_tabs, self.date_tabs.count() - 1, violations, header_text
            )
        else:
            self.update_violation_header(
                self.date_tabs, self.date_tabs.count() - 1, violations
            )

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

    def showEvent(self, event):
        """Handle tab being shown.

        Ensures the global filter is applied when switching tabs.
        """
        super().showEvent(event)
        # Apply global filter if it exists
        if hasattr(self.parent(), "global_carrier_filter"):
            text = self.parent().global_carrier_filter.text()
            if text:
                self.filter_carriers(text, "name")

    def _calculate_list_status_violation_count(self, df, list_status):
        """Calculate violations for a specific list
        status using the same logic as the main count."""
        try:
            # Find list_status column using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            if not list_status_col:
                print(f"Could not find list_status column in {df.columns.tolist()}")
                return 0

            # Filter for the specific list status (case-insensitive)
            status_mask = df[list_status_col].str.lower() == list_status.lower()
            filtered_df = df[status_mask]

            # For Summary tab, check numeric columns for any non-zero values
            if self.__class__.__name__ == "ViolationRemediesTab":
                numeric_cols = filtered_df.select_dtypes(
                    include=["float64", "int64"]
                ).columns
                exclude_cols = ["Total Hours", "Own Route Hours", "Off Route Hours"]
                violation_cols = [
                    col for col in numeric_cols if col not in exclude_cols
                ]
                return len(filtered_df[filtered_df[violation_cols].gt(0).any(axis=1)])

            # For regular violation tabs
            violation_type_col = next(
                (col for col in filtered_df.columns if col.lower() == "violation_type"),
                None,
            )
            if violation_type_col:
                return len(
                    filtered_df[
                        ~filtered_df[violation_type_col].str.contains(
                            "No Violation", na=False
                        )
                    ]
                )

            # If no violation type column, check remedy totals
            remedy_cols = ["remedy_total", "Remedy Total", "Weekly Remedy Total"]
            for col in remedy_cols:
                remedy_col = next(
                    (c for c in filtered_df.columns if c.lower() == col.lower()), None
                )
                if remedy_col:
                    return len(
                        filtered_df[
                            pd.to_numeric(filtered_df[remedy_col], errors="coerce") > 0
                        ]
                    )

            # Check for highlighted rows (violations) in any numeric columns
            numeric_cols = filtered_df.select_dtypes(
                include=["float64", "int64"]
            ).columns
            if len(numeric_cols) > 0:
                return len(filtered_df[filtered_df[numeric_cols].gt(0).any(axis=1)])

            return 0
        except Exception as e:
            print(f"Error calculating {list_status} violation count: {str(e)}")
            return 0

    def _calculate_list_status_carrier_count(self, df, list_status):
        """Calculate the number of unique carriers for a specific list status."""
        try:
            # Find list_status and carrier columns using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            carrier_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["carrier_name", "carrier name"]
                ),
                None,
            )

            if not list_status_col or not carrier_col:
                print(f"Could not find required columns in {df.columns.tolist()}")
                return 0

            # Filter for the specific list status and count unique carriers
            status_mask = df[list_status_col].str.lower() == list_status.lower()
            return len(df[status_mask][carrier_col].unique())

        except Exception as e:
            print(f"Error calculating carrier count for {list_status}: {str(e)}")
            return 0

    def _calculate_list_status_carriers_with_violations(self, df, list_status):
        """Calculate the number of unique carriers with violations for a specific list status."""
        try:
            # Find required columns using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            carrier_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["carrier_name", "carrier name"]
                ),
                None,
            )

            if not list_status_col or not carrier_col:
                print(f"Could not find required columns in {df.columns.tolist()}")
                return 0

            # Filter for the specific list status
            status_mask = df[list_status_col].str.lower() == list_status.lower()
            filtered_df = df[status_mask]

            # Get carriers with violations
            violation_type_col = next(
                (col for col in filtered_df.columns if col.lower() == "violation_type"),
                None,
            )
            if violation_type_col:
                violation_mask = ~filtered_df[violation_type_col].str.contains(
                    "No Violation", na=False
                )
                return len(filtered_df[violation_mask][carrier_col].unique())

            # If no violation type column, check remedy totals
            remedy_cols = ["remedy_total", "Remedy Total", "Weekly Remedy Total"]
            for col in remedy_cols:
                remedy_col = next(
                    (c for c in filtered_df.columns if c.lower() == col.lower()), None
                )
                if remedy_col:
                    violation_mask = (
                        pd.to_numeric(filtered_df[remedy_col], errors="coerce") > 0
                    )
                    return len(filtered_df[violation_mask][carrier_col].unique())

            return 0
        except Exception as e:
            print(
                f"Error calculating carriers with violations for {list_status}: {str(e)}"
            )
            return 0

    @staticmethod
    def format_header_text(count, is_total=True):
        """Format header text with consistent styling.

        Args:
            count: The number to display in parentheses
            is_total: If True, formats for Total Carriers,
                     if False, formats for Carriers With Violations
        """
        TOTAL_TEXT = "Total Carriers:           | "
        VIOLATIONS_TEXT = "Carriers With Violations: | "

        prefix = f"({count:02d})"
        if is_total:
            return f"{prefix} {TOTAL_TEXT}"
        else:
            return f"{prefix} {VIOLATIONS_TEXT}"

    def format_list_status_counts(self, wal, nl, otdl, ptf):
        """Format the list status counts with consistent styling.

        Args:
            wal: Count of WAL carriers
            nl: Count of NL carriers
            otdl: Count of OTDL carriers
            ptf: Count of PTF carriers

        Returns:
            str: Formatted string like "WAL: XX | NL: XX | OTDL: XX | PTF: XX"
                where XX are zero-padded two-digit numbers
        """
        return (
            f"WAL: {wal:02d} | "
            f"NL: {nl:02d} | "
            f"OTDL: {otdl:02d} | "
            f"PTF: {ptf:02d}"
        )

    def update_violation_header(
        self, tab_widget, tab_index, violation_count, custom_header_text=None
    ):
        """Update the violation count header for the current tab."""
        current_tab = tab_widget.widget(tab_index)
        if not current_tab:
            return

        # Store the current violation count
        self.current_violation_count = violation_count

        # Find or create the header widget
        header_widget = current_tab.findChild(QWidget, "violation_header_widget")
        if not header_widget:
            header_widget = QWidget(parent=current_tab)
            header_widget.setObjectName("violation_header_widget")

            # Create vertical layout for the labels
            header_layout = QVBoxLayout(header_widget)
            header_layout.setSpacing(2)
            header_layout.setContentsMargins(5, 5, 5, 5)

            # Create two labels
            total_carriers_label = QLabel(parent=header_widget)
            total_carriers_label.setObjectName("total_carriers_label")
            carriers_with_violations_label = QLabel(parent=header_widget)
            carriers_with_violations_label.setObjectName(
                "carriers_with_violations_label"
            )

            # Add labels to layout
            header_layout.addWidget(total_carriers_label)
            header_layout.addWidget(carriers_with_violations_label)

            # Style the labels
            style = """
                QLabel {
                    color: #BB86FC;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 3px 6px;
                    background-color: #1E1E1E;
                    border-radius: 3px;
                }
            """
            total_carriers_label.setStyleSheet(style)
            carriers_with_violations_label.setStyleSheet(style)

            # Add header widget to tab layout
            layout = current_tab.layout()
            if not layout:
                layout = QVBoxLayout(current_tab)
                current_tab.setLayout(layout)
            layout.insertWidget(0, header_widget)

        # Get the labels
        total_carriers_label = header_widget.findChild(QLabel, "total_carriers_label")
        carriers_with_violations_label = header_widget.findChild(
            QLabel, "carriers_with_violations_label"
        )

        # Get the current tab's data
        df = None
        table_view = current_tab.findChild(QTableView)
        if table_view and table_view.model():
            model = table_view.model()
            if isinstance(model, QSortFilterProxyModel):
                model = model.sourceModel()
            if hasattr(model, "df"):
                df = model.df

        if df is not None:
            # Find list_status column using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            if list_status_col:
                # Calculate total carriers for each list status
                ptf_carriers = self._calculate_list_status_carrier_count(df, "ptf")
                wal_carriers = self._calculate_list_status_carrier_count(df, "wal")
                nl_carriers = self._calculate_list_status_carrier_count(df, "nl")
                otdl_carriers = self._calculate_list_status_carrier_count(df, "otdl")
                total_carriers = (
                    ptf_carriers + wal_carriers + nl_carriers + otdl_carriers
                )

                # Calculate carriers with violations for each list status
                ptf_carriers_violations = (
                    self._calculate_list_status_carriers_with_violations(df, "ptf")
                )
                wal_carriers_violations = (
                    self._calculate_list_status_carriers_with_violations(df, "wal")
                )
                nl_carriers_violations = (
                    self._calculate_list_status_carriers_with_violations(df, "nl")
                )
                otdl_carriers_violations = (
                    self._calculate_list_status_carriers_with_violations(df, "otdl")
                )
                total_carriers_violations = (
                    ptf_carriers_violations
                    + wal_carriers_violations
                    + nl_carriers_violations
                    + otdl_carriers_violations
                )

                # Format the header texts using the centralized formatting methods
                total_carriers_text = self.format_header_text(
                    total_carriers, True
                ) + self.format_list_status_counts(
                    wal_carriers, nl_carriers, otdl_carriers, ptf_carriers
                )

                carriers_violations_text = self.format_header_text(
                    total_carriers_violations, False
                ) + self.format_list_status_counts(
                    wal_carriers_violations,
                    nl_carriers_violations,
                    otdl_carriers_violations,
                    ptf_carriers_violations,
                )

                total_carriers_label.setText(total_carriers_text)
                carriers_with_violations_label.setText(carriers_violations_text)
                total_carriers_label.setVisible(True)
                carriers_with_violations_label.setVisible(True)
            else:
                total_carriers_text = "No carrier data available"
                if custom_header_text:
                    carriers_violations_text = custom_header_text.replace(
                        "Total Violations", "Carriers With Violations"
                    )
                else:
                    carriers_violations_text = self.format_header_text(
                        violation_count, False
                    ) + self.format_list_status_counts(0, 0, 0, 0)
        else:
            total_carriers_text = "No carrier data available"
            if custom_header_text:
                carriers_violations_text = custom_header_text.replace(
                    "Total Violations", "Carriers With Violations"
                )
            else:
                carriers_violations_text = self.format_header_text(
                    violation_count, False
                ) + self.format_list_status_counts(0, 0, 0, 0)


class ViolationRemediesTab(BaseViolationTab):
    """Tab for displaying violation remedies summary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_name = "Summary"

    def _calculate_list_status_carrier_count(self, df, list_status):
        """Calculate the number of unique carriers
        for a specific list status in the summary view."""

        try:
            # Find list_status and carrier columns using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            carrier_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["carrier_name", "carrier name"]
                ),
                None,
            )

            if not list_status_col or not carrier_col:
                print(f"Could not find required columns in {df.columns.tolist()}")
                return 0

            # Filter for the specific list status and count unique carriers
            status_mask = df[list_status_col].str.lower() == list_status.lower()
            return len(df[status_mask][carrier_col].unique())

        except Exception as e:
            print(f"Error calculating carrier count for {list_status}: {str(e)}")
            return 0

    def _calculate_list_status_carriers_with_violations(self, df, list_status):
        """Calculate the number of unique carriers with
        violations for a specific list status in the summary view."""

        try:
            # Find required columns using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            carrier_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["carrier_name", "carrier name"]
                ),
                None,
            )

            if not list_status_col or not carrier_col:
                print(f"Could not find required columns in {df.columns.tolist()}")
                return 0

            # Filter for the specific list status
            status_mask = df[list_status_col].str.lower() == list_status.lower()
            filtered_df = df[status_mask]

            # For summary tab, check Weekly Remedy Total column
            remedy_col = next(
                (
                    col
                    for col in filtered_df.columns
                    if col.lower() == "weekly remedy total"
                ),
                None,
            )
            if remedy_col:
                violation_mask = (
                    pd.to_numeric(filtered_df[remedy_col], errors="coerce") > 0
                )
                return len(filtered_df[violation_mask][carrier_col].unique())

            return 0
        except Exception as e:
            print(
                f"Error calculating carriers with violations for {list_status}: {str(e)}"
            )
            return 0

    def _calculate_list_status_violation_count(self, df, list_status):
        """Calculate violations for a specific list status in the summary view."""
        try:
            # Find list_status column using case-insensitive lookup
            list_status_col = next(
                (
                    col
                    for col in df.columns
                    if col.lower() in ["list_status", "list status"]
                ),
                None,
            )
            if not list_status_col:
                print(f"Could not find list_status column in {df.columns.tolist()}")
                return 0

            # Filter for the specific list status
            status_mask = df[list_status_col].str.lower() == list_status.lower()
            filtered_df = df[status_mask]

            # For Summary tab, check Weekly Remedy Total column
            remedy_col = next(
                (
                    col
                    for col in filtered_df.columns
                    if col.lower() == "weekly remedy total"
                ),
                None,
            )
            if remedy_col:
                return len(
                    filtered_df[
                        pd.to_numeric(filtered_df[remedy_col], errors="coerce") > 0
                    ]
                )

            return 0
        except Exception as e:
            print(f"Error calculating {list_status} violation count: {str(e)}")
            return 0
