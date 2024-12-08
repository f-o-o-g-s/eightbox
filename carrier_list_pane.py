"""Manages the carrier list interface and related functionality.

This module provides the UI components and logic for displaying, filtering,
and managing carrier information, including their hour limits and status.
"""

# Python standard library imports
import os
import sqlite3

# Third-party imports
import pandas as pd

# PyQt5 imports
from PyQt5.QtCore import (
    QAbstractTableModel,
    QEvent,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    QVariant,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
)
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    ConfirmDialog,
    CustomErrorDialog,
    CustomNotificationDialog,
    CustomTitleBarWidget,
    NewCarriersDialog,
)
from table_utils import setup_table_copy_functionality

# Local imports
from theme import (
    COLOR_CELL_HIGHLIGHT,
    COLOR_NO_HIGHLIGHT,
    COLOR_ROW_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_WEEKLY_REMEDY,
)


class CarrierListProxyModel(QSortFilterProxyModel):
    """Custom proxy model for filtering and sorting carrier list data.

    Provides custom sorting for list status and carrier names, along with
    filtering capabilities for both status and text searches.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_filter = ""
        self.text_filter = ""
        # Define status order for sorting
        self.status_order = {"nl": 0, "wal": 1, "otdl": 2, "ptf": 3}

    def lessThan(self, left, right):
        """Custom sorting implementation"""
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        # Get column name
        column_name = self.sourceModel().headerData(
            left.column(), Qt.Horizontal, Qt.DisplayRole
        )

        if column_name == "list_status":
            # Use custom status ordering
            left_order = self.status_order.get(str(left_data).lower(), 999)
            right_order = self.status_order.get(str(right_data).lower(), 999)
            if left_order != right_order:
                return left_order < right_order
            else:
                # If list_status is the same, sort by carrier_name
                carrier_col = self.sourceModel().df.columns.get_loc("carrier_name")
                left_carrier = str(
                    self.sourceModel().data(
                        self.sourceModel().index(left.row(), carrier_col),
                        Qt.DisplayRole,
                    )
                ).lower()
                right_carrier = str(
                    self.sourceModel().data(
                        self.sourceModel().index(right.row(), carrier_col),
                        Qt.DisplayRole,
                    )
                ).lower()
                return left_carrier < right_carrier
        else:
            # For carrier_name column, ensure ascending order
            if column_name == "carrier_name":
                return str(left_data).lower() < str(right_data).lower()
            # For other columns, use standard comparison
            return str(left_data).lower() < str(right_data).lower()

    def set_status_filter(self, status):
        """Set the status filter for the proxy model.

        Args:
            status (str): The list status to filter by ('all', 'otdl', 'wal', 'nl', 'ptf')
                         Use 'all' to clear the filter.
        """
        self.status_filter = status.lower() if status != "all" else ""
        self.invalidateFilter()

    def set_text_filter(self, text):
        """Set the text filter for the proxy model.

        Args:
            text (str): The text to filter carrier names by.
                       Case-insensitive partial matching is supported.
        """
        self.text_filter = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Determine if a row should be included in the filtered results.

        Implements both status and text filtering logic. A row is accepted if it:
        1. Matches the current status filter (if any)
        2. Contains the filter text in any column (if text filter is active)

        Args:
            source_row (int): Row index in the source model
            source_parent (QModelIndex): Parent index in source model

        Returns:
            bool: True if row should be shown, False if it should be filtered out
        """
        source_model = self.sourceModel()

        # Get the list status for this row
        status_idx = source_model.index(
            source_row,
            self.sourceModel().df.columns.get_loc("list_status"),
            source_parent,
        )
        status = str(source_model.data(status_idx, Qt.DisplayRole)).lower()

        # Check status filter
        if self.status_filter and status != self.status_filter:
            return False

        # If there's no text filter, we're done
        if not self.text_filter:
            return True

        # Check text filter against all columns
        for column in range(source_model.columnCount(source_parent)):
            idx = source_model.index(source_row, column, source_parent)
            data = str(source_model.data(idx, Qt.DisplayRole)).lower()
            if self.text_filter in data:
                return True

        return False


class PandasTableModel(QAbstractTableModel):
    """Table model for displaying pandas DataFrame in a QTableView.

    Handles data display, editing, and formatting for carrier information
    including status colors and text alignment.
    """

    def __init__(self, df, db_df=None, parent=None):
        super().__init__(parent)
        self.status_order = {"nl": 0, "wal": 1, "otdl": 2, "ptf": 3}
        self.df = df
        self.db_df = db_df if db_df is not None else pd.DataFrame()

    def update_data(self, new_df, new_db_df=None):
        """Update the model's data with new DataFrame(s).

        Args:
            new_df (pd.DataFrame): New carrier data to display
            new_db_df (pd.DataFrame, optional): New database reference data
        """
        self.beginResetModel()
        self.df = new_df
        if new_db_df is not None:
            self.db_df = new_db_df
        self.endResetModel()

    def rowCount(self, parent=None):
        """Get the number of rows in the model.

        Args:
            parent (QModelIndex): Parent index (unused in table models)

        Returns:
            int: Number of rows in the carrier data
        """
        return len(self.df)

    def columnCount(self, parent=None):
        """Get the number of columns in the model.

        Args:
            parent (QModelIndex): Parent index (unused in table models)

        Returns:
            int: Number of columns in the carrier data
        """
        return len(self.df.columns)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            value = self.df.iloc[index.row(), index.column()]
            return str(value) if pd.notna(value) else ""

        if role == Qt.ForegroundRole:
            list_status = self.df.iloc[
                index.row(), self.df.columns.get_loc("list_status")
            ]
            if list_status == "nl":  # Assuming "nl" is the bright green
                return QBrush(QColor("#000000"))  # Black text for better contrast
            return QBrush(COLOR_TEXT_LIGHT)

        if role == Qt.BackgroundRole:
            # Apply background color based on `list_status`
            list_status = self.df.iloc[
                index.row(), self.df.columns.get_loc("list_status")
            ]
            status_color_mapping = {
                "otdl": COLOR_ROW_HIGHLIGHT,
                "wal": COLOR_CELL_HIGHLIGHT,
                "nl": COLOR_WEEKLY_REMEDY,
                "ptf": COLOR_NO_HIGHLIGHT,
            }
            return QBrush(status_color_mapping.get(list_status, QColor(Qt.white)))

        return QVariant()

    def headerData(self, section, orientation, role):
        """Get header data for display.

        Provides column and row headers for the carrier list table.

        Args:
            section (int): Section (row/column) number
            orientation (Qt.Orientation): Header orientation
            role (Qt.ItemDataRole): Data role being requested

        Returns:
            str: Header text for DisplayRole, None for other roles
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.df.columns[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        """Set data in the model.

        Updates the model data and handles any necessary post-update actions.

        Args:
            index (QModelIndex): The index to update
            value (Any): The new value to set
            role (Qt.ItemRole): The role being set (default: EditRole)

        Returns:
            bool: True if data was successfully set, False otherwise
        """
        if role == Qt.EditRole and index.isValid():
            column = self.df.columns[index.column()]
            current_value = self.df.iloc[index.row(), index.column()]

            if current_value != value:
                self.df.iloc[index.row(), index.column()] = value

                # Track changed rows
                if not hasattr(self, "changed_rows"):
                    self.changed_rows = set()
                self.changed_rows.add(index.row())

                # Notify the view of data changes
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.BackgroundRole])
                print(f"Edited {column} for row {index.row()}, new value: {value}")
                return True
        return False

    def flags(self, index):
        """Return item flags for the given index.

        Enables selection and editing for all cells in the table.

        Args:
            index (QModelIndex): Index to get flags for

        Returns:
            Qt.ItemFlags: Flags indicating item capabilities
        """
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable


class CarrierListPane(QWidget):
    """Main widget for managing carrier list interface.

    Provides functionality for displaying, filtering, editing, and managing
    carrier information including their list status and hour limits.

    Signals:
        data_updated: Emitted when carrier data is modified
        reload_requested: Emitted when application reload is needed
        request_apply_date_range: Emitted when date range should be applied
        carrier_list_updated: Emitted when carrier list is modified
    """

    data_updated = pyqtSignal(pd.DataFrame)  # Signal to notify about data changes
    reload_requested = pyqtSignal()  # Signal to request application reload
    request_apply_date_range = pyqtSignal()  # New signal
    carrier_list_updated = pyqtSignal(pd.DataFrame)  # Add this signal

    def __init__(
        self,
        mandates_db_path,
        otdl_maximization_pane=None,
        fetch_clock_ring_data_callback=None,
        parent=None,
    ):
        super().__init__(parent)
        self.parent_widget = parent
        self.parent_main = parent

        # Initialize data
        self.mandates_db_path = mandates_db_path
        self.json_path = "carrier_list.json"

        # Load and pre-sort the carrier data
        df = self.load_carrier_list()
        # Create categorical type for list_status with custom order
        status_order = ["nl", "wal", "otdl", "ptf"]
        df["list_status"] = pd.Categorical(
            df["list_status"], categories=status_order, ordered=True
        )
        # Sort by list_status first, then carrier_name
        self.carrier_df = df.sort_values(
            ["list_status", "carrier_name"], ascending=[True, True]
        ).reset_index(drop=True)
        self.temp_df = self.carrier_df.copy()

        # Set window flags
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # No margins for main layout
        main_layout.setSpacing(0)  # No spacing for main layout

        # Add title bar
        title_bar = CustomTitleBarWidget(title="Carrier List Setup", parent=self)
        main_layout.addWidget(title_bar)

        # Create content widget with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)  # Add padding around content
        content_layout.setSpacing(10)  # Add spacing between elements

        # Add filter input with material styling
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by carrier name...")
        self.filter_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #2D2D2D;
                color: #E1E1E1;
                border: 1px solid #333333;
                padding: 8px;
                border-radius: 4px;
                margin-bottom: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #BB86FC;
            }
        """
        )
        content_layout.addWidget(self.filter_input)

        # Add table view with material styling
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(
            QTableView.SelectRows
        )  # Select entire rows
        self.table_view.setSelectionMode(
            QTableView.SingleSelection
        )  # Optional: limit to one row at a time
        self.table_view.setStyleSheet(
            """
            QTableView {
                background-color: #1E1E1E;
                alternate-background-color: #262626;
                gridline-color: #333333;
                border: 1px solid #333333;
                border-radius: 4px;
                selection-background-color: #3700B3;
                selection-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E1E1E1;
                padding: 8px;
                border: none;
                border-right: 1px solid #333333;
                border-bottom: 1px solid #333333;
            }
            QTableView::item {
                padding: 4px;
            }
        """
        )

        # Add table view with proper model setup
        self.main_model = PandasTableModel(self.carrier_df)
        self.proxy_model = CarrierListProxyModel(self)
        self.proxy_model.setSourceModel(self.main_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)

        # Force initial sort by list_status
        list_status_col = self.carrier_df.columns.get_loc("list_status")
        self.proxy_model.sort(list_status_col, Qt.AscendingOrder)

        content_layout.addWidget(self.table_view)

        # Style for all buttons using material design
        button_style = """
            QPushButton {
                background-color: #BB86FC;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """

        # Create button container with spacing
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin
        button_layout.setSpacing(8)  # Space between buttons

        # Add buttons with material styling
        edit_button = QPushButton("Edit Carrier")
        edit_button.setStyleSheet(button_style)
        edit_button.clicked.connect(self.edit_carrier)
        button_layout.addWidget(edit_button)

        remove_button = QPushButton("Remove Carrier")
        remove_button.setStyleSheet(button_style)
        remove_button.clicked.connect(self.remove_carrier)
        button_layout.addWidget(remove_button)

        save_button = QPushButton("Save/Apply")
        save_button.setStyleSheet(button_style)
        save_button.clicked.connect(self.save_to_json)
        button_layout.addWidget(save_button)

        # Add button container to content layout
        content_layout.addWidget(button_container)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)

        # Set the layout
        self.setLayout(main_layout)

        # Connect filter input
        self.filter_input.textChanged.connect(self.apply_filter)

        # Set minimum size
        self.setMinimumSize(300, 700)

        # Create statistics panel with Material Design styling and hover effects
        stats_panel = QWidget()
        stats_panel.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                border-top: 1px solid #333333;
                padding: 8px;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 13px;
                padding: 4px;
            }
            QLabel[class="stat-value"] {
                color: #BB86FC;
                font-weight: bold;
            }
            QWidget[class="stat-container"] {
                border-radius: 4px;
                padding: 4px 8px;
            }
            QWidget[class="stat-container"]:hover {
                background-color: #333333;
                cursor: pointer;
            }
            QWidget[class="stat-container"][selected="true"] {
                background-color: #3700B3;
            }
        """
        )
        stats_layout = QHBoxLayout(stats_panel)
        stats_layout.setSpacing(20)  # Space between stat items

        # Create labels for statistics
        self.total_label = QLabel("Total Carriers: ")
        self.total_value = QLabel("0")
        self.total_value.setProperty("class", "stat-value")

        self.otdl_label = QLabel("OTDL: ")
        self.otdl_value = QLabel("0")
        self.otdl_value.setProperty("class", "stat-value")

        self.wal_label = QLabel("WAL: ")
        self.wal_value = QLabel("0")
        self.wal_value.setProperty("class", "stat-value")

        self.nl_label = QLabel("NL: ")
        self.nl_value = QLabel("0")
        self.nl_value.setProperty("class", "stat-value")

        self.ptf_label = QLabel("PTF: ")
        self.ptf_value = QLabel("0")
        self.ptf_value.setProperty("class", "stat-value")

        # Create clickable stat containers with visual feedback
        for label_text, value_widget, status in [
            ("ALL Carriers: ", self.total_value, "all"),
            ("OTDL: ", self.otdl_value, "otdl"),
            ("WAL: ", self.wal_value, "wal"),
            ("NL: ", self.nl_value, "nl"),
            ("PTF: ", self.ptf_value, "ptf"),
        ]:
            stat_container = QWidget()
            stat_container.setProperty("class", "stat-container")
            stat_container.setProperty("selected", False)
            stat_layout = QHBoxLayout(stat_container)
            stat_layout.setContentsMargins(4, 4, 4, 4)

            label = QLabel(label_text)
            stat_layout.addWidget(label)
            stat_layout.addWidget(value_widget)

            # Store the filter status with the widget
            stat_container.status = status

            # Make the container clickable
            stat_container.mousePressEvent = lambda e, s=status: self.filter_by_status(
                s
            )

            stats_layout.addWidget(stat_container)

            # Store reference to container for updating selection state
            setattr(self, f"{status}_container", stat_container)

        # Add stretch to push stats to the left
        stats_layout.addStretch()

        # Add stats panel to the main layout before the button container
        content_layout.addWidget(stats_panel)

        # Add method to update statistics
        self.update_statistics()

        # Connect model changes to statistics updates
        self.proxy_model.layoutChanged.connect(self.update_statistics)
        self.filter_input.textChanged.connect(self.update_statistics)

    def minimize_to_button(self):
        """Custom minimize handler that properly hides the window"""
        if self.parent_main and hasattr(self.parent_main, "carrier_list_button"):
            self.parent_main.carrier_list_button.setChecked(False)
        self.hide()

    def changeEvent(self, event):
        """Handle window state changes, particularly minimization.

        Args:
            event (QEvent): The window state change event
        """
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Prevent actual minimize, use our custom handler instead
                self.minimize_to_button()
                event.accept()
        super().changeEvent(event)

    def hideEvent(self, event):
        """Handle window hide events.

        Updates the parent window's carrier list button state when
        this pane is hidden.

        Args:
            event (QEvent): The hide event
        """
        try:
            # Check if we have a parent widget and if it has the carrier_list_button
            if (
                hasattr(self, "parent_widget")
                and self.parent_widget is not None
                and hasattr(self.parent_widget, "carrier_list_button")
            ):
                self.parent_widget.carrier_list_button.setChecked(False)
        except AttributeError:
            # Silently handle the case where the button doesn't exist
            pass

        # Always call the parent class's hideEvent
        super().hideEvent(event)

    def initUI(self, layout):
        """Initialize the user interface components.

        Sets up the table view, filter input, and control buttons.
        Configures the layout and styling of all UI elements.

        Args:
            layout (QLayout): The layout to populate with UI elements
        """
        layout.setContentsMargins(10, 10, 10, 10)

        # Initialize the main table view for the Carrier List tab
        self.table_view = QTableView()
        self.table_view.setEditTriggers(
            QTableView.NoEditTriggers
        )  # Disable inline editing
        self.main_model = PandasTableModel(self.temp_df, parent=self)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.main_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setSortRole(Qt.UserRole)  # Custom sorting role for list_status
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)

        # Add copy functionality
        setup_table_copy_functionality(self.table_view)

        layout.addWidget(self.table_view)

        # Filter input field
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by carrier name or list status...")
        self.filter_input.textChanged.connect(self.apply_filter)
        layout.addWidget(self.filter_input)

        # Buttons for editing, removing, saving, and applying changes
        edit_button = QPushButton("Edit Carrier")
        edit_button.clicked.connect(self.edit_carrier)
        layout.addWidget(edit_button)

        remove_button = QPushButton("Remove Carrier")
        remove_button.clicked.connect(self.remove_carrier)
        layout.addWidget(remove_button)

        save_button = QPushButton("Save/Apply Carrier List")
        save_button.clicked.connect(self.save_to_json)
        layout.addWidget(save_button)

        self.table_view.setSelectionBehavior(
            QTableView.SelectRows
        )  # Highlight entire row on cell selection
        self.setLayout(layout)

    def save_to_json(self):
        """Save the current carrier list to JSON file.

        Saves the current state of the carrier list and emits appropriate
        signals to update other components. Shows notification dialogs for
        success or failure.
        """
        try:
            self.main_model.df.to_json(self.json_path, orient="records")
            CustomNotificationDialog.show_notification(
                self, "Success", "Carrier list has been saved."
            )

            # Check if date selection pane exists and has a date selected
            parent = self.parent()
            if (
                hasattr(parent, "date_selection_pane")
                and parent.date_selection_pane is not None
                and parent.date_selection_pane.calendar.selectedDate().isValid()
            ):
                # Only emit signals if we have a valid date
                self.carrier_list_updated.emit(self.main_model.df)
                self.request_apply_date_range.emit()
            else:
                CustomNotificationDialog.show_notification(
                    self,
                    "Note",
                    "Carrier list saved. Select a date range to view updated violations.",
                )

        except Exception as e:
            CustomNotificationDialog.show_notification(
                self, "Error", f"Failed to save carrier list: {e}"
            )

    def load_carrier_list(self):
        """Load and process carrier list data.

        Attempts to load from JSON file first, falls back to database if needed.
        Handles data validation, default values, and checks for new carriers.

        Returns:
            pd.DataFrame: Processed carrier list data with all required columns
        """
        # Define default columns and their types
        default_columns = {
            "carrier_name": str,
            "list_status": str,
            "route_s": str,
            "hour_limit": str,
            "effective_date": str,
        }

        # Load initial data
        if os.path.exists(self.json_path):
            try:
                df = pd.read_json(self.json_path, orient="records")
            except Exception as e:
                CustomNotificationDialog.show_notification(
                    self, "Error", f"Failed to load JSON file: {e}"
                )
                df = self.fetch_carrier_data()
        else:
            df = self.fetch_carrier_data()

        # Ensure all required columns exist with default values
        for col, dtype in default_columns.items():
            if col not in df.columns:
                df[col] = None if dtype == str else dtype()

        # Set default values for missing data
        df["list_status"] = df["list_status"].fillna("nl")  # Default to no-list
        df["route_s"] = df["route_s"].fillna("")
        df["hour_limit"] = df["hour_limit"].fillna("12hr")  # Default to 12 hours

        # Ensure datetime formatting
        df["effective_date"] = pd.to_datetime(df["effective_date"]).fillna(
            pd.Timestamp.now()
        )

        # Create status order mapping
        status_order = {"nl": 0, "wal": 1, "otdl": 2, "ptf": 3}
        df["_status_order"] = df["list_status"].map(status_order)

        # Sort by status order first, then alphabetically by carrier name
        df = df.sort_values(["_status_order", "carrier_name"], ascending=[True, True])

        # Drop the temporary sorting column
        df = df.drop(columns=["_status_order"])

        # Format the date after sorting
        df["effective_date"] = df["effective_date"].dt.strftime("%Y-%m-%d")
        df = df.reset_index(drop=True)

        # Fetch the latest data from the database
        db_data = self.fetch_carrier_data()

        # Identify new carriers in the database that are not in the JSON file
        new_carriers = db_data[~db_data["carrier_name"].isin(df["carrier_name"])]
        if not new_carriers.empty:
            new_carrier_names = new_carriers["carrier_name"].tolist()
            QTimer.singleShot(
                100,
                lambda: self.show_new_carriers_dialog(
                    new_carriers, new_carrier_names, df
                ),
            )

        return df

    def show_new_carriers_dialog(self, new_carriers, new_carrier_names, df):
        """Display dialog for handling newly discovered carriers.

        Shows a dialog allowing user to select which new carriers to add
        to the list and handles updating the data accordingly.

        Args:
            new_carriers (pd.DataFrame): DataFrame containing new carrier data
            new_carrier_names (list): List of new carrier names
            df (pd.DataFrame): Current carrier list DataFrame
        """
        # Show custom dialog and get selected carriers
        selected_carriers = NewCarriersDialog.get_new_carriers(
            self.parent_widget, new_carrier_names
        )

        if selected_carriers:
            # Add selected carriers to the DataFrame
            selected_data = new_carriers[
                new_carriers["carrier_name"].isin(selected_carriers)
            ]
            updated_df = pd.concat([df, selected_data], ignore_index=True)

            # Update the model with the new data
            self.main_model.update_data(updated_df)

            # Save the updated list to JSON immediately
            try:
                updated_df.to_json(self.json_path, orient="records")

                # Emit signals to update the main application
                self.carrier_list_updated.emit(updated_df)
                self.data_updated.emit(updated_df)

                # If we have a valid date selected, trigger a refresh
                if (
                    hasattr(self.parent_widget, "date_selection_pane")
                    and self.parent_widget.date_selection_pane is not None
                    and self.parent_widget.date_selection_pane.calendar.selectedDate().isValid()
                ):
                    self.request_apply_date_range.emit()

            except Exception as e:
                CustomErrorDialog.error(
                    self, "Error", f"Failed to save updated carrier list: {e}"
                )
                return

            CustomNotificationDialog.show_notification(
                self,
                "Success",
                f"{len(selected_carriers)} carriers have been added to the list. "
                "Please open the Carrier List to review your changes.",
            )

            # Update statistics
            self.update_statistics()

    def edit_carrier(self):
        """Edit the selected carrier's details.

        Opens a dialog allowing modification of carrier list status and hour limits.
        Updates the model and view with any changes made.
        """
        selected_index = self.table_view.currentIndex()
        if not selected_index.isValid():
            CustomNotificationDialog.show_notification(
                self, "No Selection", "Please select a carrier to edit."
            )
            return

        # Map the selected index back to the DataFrame index
        source_index = self.proxy_model.mapToSource(selected_index)
        row = source_index.row()

        # Get the correct row index in the sorted DataFrame
        sorted_df_index = self.main_model.df.index[row]

        # Fetch existing values for the carrier using the correct index
        carrier_data = self.main_model.df.loc[sorted_df_index].to_dict()

        # Create an edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Carrier")
        layout = QVBoxLayout()

        # Carrier name input
        name_label = QLabel("Carrier Name:")
        name_input = QLineEdit(carrier_data["carrier_name"])
        name_input.setReadOnly(
            True
        )  # Ensure the carrier name is not editable to avoid mismatched updates
        layout.addWidget(name_label)
        layout.addWidget(name_input)

        # List status dropdown
        list_status_label = QLabel("List Status:")
        list_status_dropdown = QComboBox()
        list_status_dropdown.addItems(["otdl", "ptf", "wal", "nl"])
        list_status_dropdown.setCurrentText(carrier_data["list_status"])
        layout.addWidget(list_status_label)
        layout.addWidget(list_status_dropdown)

        # Hour limit dropdown
        hour_limit_label = QLabel("Hour Limit:")
        hour_limit_dropdown = QComboBox()
        layout.addWidget(hour_limit_label)
        layout.addWidget(hour_limit_dropdown)

        # Populate the hour_limit_dropdown based on initial list_status
        def update_hour_limit_options():
            hour_limit_dropdown.clear()
            if list_status_dropdown.currentText() == "otdl":
                hour_limit_dropdown.addItems(["12hr", "11hr", "10hr"])
            else:
                hour_limit_dropdown.addItems(["12hr", "11hr", "10hr", "(none)"])

        update_hour_limit_options()
        list_status_dropdown.currentTextChanged.connect(update_hour_limit_options)

        # Ensure `hour_limit` is a string and set the current selection
        current_hour_limit = carrier_data["hour_limit"] or "(none)"
        if str(current_hour_limit) in hour_limit_dropdown.itemText(
            hour_limit_dropdown.currentIndex()
        ):
            hour_limit_dropdown.setCurrentText(str(current_hour_limit))
        else:
            hour_limit_dropdown.setCurrentText("(none)")

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Handle dialog actions
        def on_accept():
            # Update the DataFrame with new values
            new_list_status = list_status_dropdown.currentText()
            selected_hour_limit = hour_limit_dropdown.currentText()
            self.main_model.df.loc[sorted_df_index, "list_status"] = new_list_status
            self.main_model.df.loc[sorted_df_index, "hour_limit"] = (
                None if selected_hour_limit == "(none)" else selected_hour_limit
            )

            # Refresh the proxy model
            self.main_model.update_data(self.main_model.df)
            self.proxy_model.invalidate()  # Ensure the proxy model refreshes
            dialog.accept()

        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()

    def remove_carrier(self):
        """Remove the selected carrier from the list.

        Shows confirmation dialog before removal. Updates the model,
        JSON file, and emits appropriate signals after successful removal.
        """
        try:
            selected_index = self.table_view.selectionModel().currentIndex()
            if not selected_index.isValid():
                CustomNotificationDialog.show_notification(
                    self, "No Selection", "Please select a carrier to remove."
                )
                return

            # Map the selected index to the source model
            source_index = self.proxy_model.mapToSource(selected_index)
            row = source_index.row()

            # Get the correct row index in the sorted DataFrame
            sorted_df_index = self.main_model.df.index[row]

            # Fetch the carrier name using the correct index
            carrier_name = self.main_model.df.loc[sorted_df_index, "carrier_name"]

            # Create and show custom confirmation dialog
            confirm_dialog = ConfirmDialog(
                f"Are you sure you want to remove carrier '{carrier_name}'?", self
            )
            if confirm_dialog.exec_() == QDialog.Accepted:
                # Drop the row from the DataFrame using the correct index
                self.main_model.df.drop(index=sorted_df_index, inplace=True)
                self.main_model.df.reset_index(drop=True, inplace=True)

                # Update the JSON file to reflect the change
                try:
                    self.main_model.df.to_json(self.json_path, orient="records")
                except Exception as e:
                    CustomErrorDialog.error(
                        self, "Error", f"Failed to update the JSON file: {e}"
                    )
                    return

                # Update the table view
                self.main_model.update_data(self.main_model.df)

                # Emit the signal when data is updated
                self.data_updated.emit(self.main_model.df)

                CustomNotificationDialog.show_notification(
                    self, "Success", f"Carrier '{carrier_name}' removed successfully."
                )

                # Clear the selection after removal
                self.table_view.clearSelection()

        except Exception as e:
            CustomErrorDialog.error(
                self, "Error", f"An error occurred while removing the carrier: {e}"
            )
            # Ensure the UI is in a good state
            self.table_view.clearSelection()

    def highlight_changes(self, top_left=None, bottom_right=None, roles=None):
        """Highlight cells that have been modified.

        Compares current values with original values and applies
        visual highlighting to changed cells.

        Args:
            top_left (QModelIndex, optional): Starting index of change range
            bottom_right (QModelIndex, optional): Ending index of change range
            roles (list, optional): List of item roles that were changed
        """

        for row in range(self.temp_df.shape[0]):
            for col in range(self.temp_df.shape[1]):
                # Get the original and temporary values
                original_value = self.carrier_df.iloc[row, col]
                temp_value = self.temp_df.iloc[row, col]

                # Map the row/col through the proxy model to the source model
                source_index = self.proxy_model.mapToSource(
                    self.proxy_model.index(row, col)
                )

                if original_value != temp_value:
                    print(f"Highlighting Row {row}, Col {col} as modified.")
                    self.main_model.setData(
                        source_index, QColor("#FFF59D"), Qt.BackgroundRole
                    )
                else:
                    self.main_model.setData(
                        source_index, QColor(Qt.white), Qt.BackgroundRole
                    )

    def minimize(self):
        """Hide the pane and send it back to the main GUI."""
        self.hide()
        if self.parent_widget:
            self.parent_widget.reenable_carrier_list_button()

    def init_tabs(self):
        """Initialize the carrier list and summary tabs.

        Creates and configures the tab widget with carrier list
        and summary views.
        """
        # Clear existing tabs to prevent duplication
        while self.summary_tab_widget.count():
            self.summary_tab_widget.removeTab(0)

        # Add the Carrier List tab
        carrier_list_widget = QWidget()
        carrier_list_layout = QVBoxLayout()
        carrier_list_layout.addWidget(self.table_view)  # Use the existing table view
        carrier_list_widget.setLayout(carrier_list_layout)
        self.summary_tab_widget.addTab(carrier_list_widget, "Carrier List")

        # Add the Summary tab
        summary_widget = QWidget()
        summary_layout = QVBoxLayout()
        self.summary_table_view = QTableView()  # A separate view for summary data
        self.update_summary()  # Populate the summary table initially
        summary_layout.addWidget(self.summary_table_view)
        summary_widget.setLayout(summary_layout)
        self.summary_tab_widget.addTab(summary_widget, "Summary")

    def reset_highlights(self):
        """Remove all cell highlighting from the table.

        Resets background colors to default after changes are confirmed.
        """
        print("Resetting highlights...")
        for row in range(self.carrier_df.shape[0]):
            for col in range(self.carrier_df.shape[1]):
                source_index = self.proxy_model.mapToSource(
                    self.proxy_model.index(row, col)
                )
                self.main_model.setData(
                    source_index, QColor(Qt.white), Qt.BackgroundRole
                )

    def init_carrier_list_tab(self):
        """Initialize the carrier list tab interface.

        Sets up the filter input, table view, and control buttons
        for the carrier list tab.
        """
        layout = QVBoxLayout()

        # Add a filter input field
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by carrier name or list status...")
        layout.addWidget(self.filter_input)

        # Table view for carrier list
        self.table_view = QTableView()
        self.model = PandasTableModel(self.carrier_df)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)

        # Connect filter input
        self.filter_input.textChanged.connect(self.apply_filter)

        layout.addWidget(self.table_view)
        self.carrier_list_widget.setLayout(layout)

        # Add buttons for Save and Check for Changes
        button_layout = QVBoxLayout()

        save_button = QPushButton("Save Carrier List to JSON")
        save_button.clicked.connect(self.save_to_json)
        button_layout.addWidget(save_button)

        check_button = QPushButton("Check for Changes")
        check_button.clicked.connect(self.check_for_changes)
        button_layout.addWidget(check_button)

        # Add buttons below the table view
        layout.addLayout(button_layout)

        self.carrier_list_widget.setLayout(layout)

    def init_summary_tab(self):
        """Initialize the summary tab interface.

        Creates and configures the summary view showing aggregated
        carrier information.
        """
        layout = QVBoxLayout()

        # Summary table view
        self.summary_table_view = QTableView()
        self.update_summary()  # Populate the summary table initially

        layout.addWidget(self.summary_table_view)
        self.summary_widget.setLayout(layout)

    def fetch_carrier_data(self):
        """Fetch carrier data from the mandates database.

        Retrieves carrier information excluding those with 'out of station' status.

        Returns:
            pd.DataFrame: Carrier data with columns for name, effective date,
                         list status, and route information
        """
        query = """
        SELECT
            carrier_name,
            -- Format effective_date to exclude timestamp
            DATE(MAX(effective_date)) AS effective_date,
            list_status,
            route_s,
            station
        FROM carriers
        GROUP BY carrier_name
        """
        try:
            with sqlite3.connect(self.mandates_db_path) as conn:
                df = pd.read_sql_query(query, conn)

                # Filter out carriers with "out of station"
                df = df[
                    ~df["station"].str.contains("out of station", case=False, na=False)
                ]

                # Convert effective_date to string (YYYY-MM-DD) for uniform formatting
                df["effective_date"] = pd.to_datetime(df["effective_date"]).dt.strftime(
                    "%Y-%m-%d"
                )

                # Drop the station column after filtering to maintain the original structure
                df.drop(columns=["station"], inplace=True)

                return df

        except Exception as e:
            CustomNotificationDialog.show_notification(self, "Database Error", str(e))
            return pd.DataFrame(
                columns=["carrier_name", "effective_date", "list_status", "route_s"]
            )

    def update_statistics(self):
        """Update the carrier statistics display.

        Calculates and displays counts for each list status category
        and updates the visual state of status filters.
        """
        if self.proxy_model and self.proxy_model.sourceModel():
            # Get counts from the full dataset
            full_df = self.main_model.df
            total_carriers = len(full_df)
            otdl_total = len(full_df[full_df["list_status"] == "otdl"])
            wal_total = len(full_df[full_df["list_status"] == "wal"])
            nl_total = len(full_df[full_df["list_status"] == "nl"])
            ptf_total = len(full_df[full_df["list_status"] == "ptf"])

            # Update labels with total counts
            self.total_value.setText(str(total_carriers))
            self.otdl_value.setText(str(otdl_total))
            self.wal_value.setText(str(wal_total))
            self.nl_value.setText(str(nl_total))
            self.ptf_value.setText(str(ptf_total))

            # Update the visual selection state based on the current status filter
            current_status = self.proxy_model.status_filter
            for status in ["all", "otdl", "wal", "nl", "ptf"]:
                container = getattr(self, f"{status}_container")
                is_selected = (status == "all" and not current_status) or (
                    status == current_status
                )
                container.setProperty("selected", is_selected)
                container.style().unpolish(container)
                container.style().polish(container)

    def filter_by_status(self, status):
        """Filter the carrier list by selected status.

        Updates the visual state of status filters and applies
        the selected filter to the view.

        Args:
            status (str): The status to filter by ('all', 'otdl', 'wal', 'nl', 'ptf')
        """
        # Clear previous selection states
        for s in ["all", "otdl", "wal", "nl", "ptf"]:
            container = getattr(self, f"{s}_container")
            container.setProperty("selected", False)
            container.style().unpolish(container)
            container.style().polish(container)

        # Set new selection state
        container = getattr(self, f"{status}_container")
        container.setProperty("selected", True)
        container.style().unpolish(container)
        container.style().polish(container)

        # Clear the text filter input
        self.filter_input.clear()

        # Apply the status filter using our custom proxy model
        self.proxy_model.set_status_filter(status)

        # Force update of statistics
        self.update_statistics()

    def apply_filter(self):
        """Apply the current text filter to the carrier list.

        Updates the proxy model filter based on the current text input
        and refreshes the statistics display.
        """
        filter_text = self.filter_input.text()
        self.proxy_model.set_text_filter(filter_text)
        self.update_statistics()
