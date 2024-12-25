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
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    ConfirmDialog,
    CustomErrorDialog,
    CustomNotificationDialog,
    CustomTitleBarWidget,
    CustomWarningDialog,
    NewCarriersDialog,
)
from table_utils import setup_table_copy_functionality
from theme import (
    COLOR_TEXT_DIM,
    COLOR_TEXT_LIGHT,
    MATERIAL_BACKGROUND,
    MATERIAL_PRIMARY,
    MATERIAL_SURFACE,
)


class RightAlignDelegate(QStyledItemDelegate):
    """Custom delegate for right-aligned text in table cells."""

    def initStyleOption(self, option, index):
        """Initialize style options for the delegate.

        Args:
            option (QStyleOptionViewItem): The style options to initialize
            index (QModelIndex): The index being styled
        """
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignRight | Qt.AlignVCenter


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

    def set_text_filter(self, text):
        """Set the text filter and invalidate the current filtering."""
        self.text_filter = text.lower()
        self.invalidateFilter()

    def set_status_filter(self, status):
        """Set the status filter and invalidate the current filtering."""
        self.status_filter = status if status != "all" else ""
        self.invalidateFilter()

    def less_than(self, left, right):
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

        # For carrier_name column, ensure ascending order
        if column_name == "carrier_name":
            return str(left_data).lower() < str(right_data).lower()
        # For other columns, use standard comparison
        return str(left_data).lower() < str(right_data).lower()

    def filter_accepts_row(self, source_row, source_parent):
        """Determine if a row should be included in the filtered results."""
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

    # Alias Qt method names to maintain compatibility
    lessThan = less_than
    filterAcceptsRow = filter_accepts_row


class PandasTableModel(QAbstractTableModel):
    """Table model for displaying pandas DataFrame in a QTableView.

    Handles data display, editing, and formatting for carrier information
    including status colors and text alignment.
    """

    def __init__(self, df, db_df=None, parent=None):
        super().__init__(parent)
        self.df = df
        self.db_df = db_df if db_df is not None else pd.DataFrame()
        # Define text colors for different list statuses
        self.status_text_colors = {
            "otdl": QColor("#BB86FC"),  # Purple
            "wal": QColor("#03DAC6"),  # Teal
            "nl": QColor("#64DD17"),  # Light Green
            "ptf": QColor("#FF7597"),  # Pink
        }

    def calculate_text_color(self, bg_color):
        """Calculate optimal text color (black or white) based on background color.

        Uses relative luminance formula to determine best contrast.

        Args:
            bg_color (QColor): Background color to calculate against

        Returns:
            QColor: Either black or white depending on background
        """
        # Convert RGB values to relative luminance
        r = bg_color.red() / 255.0
        g = bg_color.green() / 255.0
        b = bg_color.blue() / 255.0

        # Calculate relative luminance using sRGB formula
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Return white for dark backgrounds, black for light backgrounds
        return QColor("#FFFFFF") if luminance < 0.5 else QColor("#000000")

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

    def row_count(self, parent=None):
        """Get the number of rows in the model.

        Args:
            parent (QModelIndex): Parent index (unused in table models)

        Returns:
            int: Number of rows in the carrier data
        """
        return len(self.df)

    def column_count(self, parent=None):
        """Get the number of columns in the model.

        Args:
            parent (QModelIndex): Parent index (unused in table models)

        Returns:
            int: Number of columns in the carrier data
        """
        return len(self.df.columns)

    def data(self, index, role=Qt.DisplayRole):
        """Get data for the specified model index and role."""
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            value = self.df.iloc[index.row(), index.column()]
            # Format hour_limit with 2 decimal places
            if self.df.columns[index.column()] == "hour_limit":
                return f"{float(value):.2f}" if pd.notna(value) else ""
            return str(value) if pd.notna(value) else ""

        elif role == Qt.ForegroundRole:
            # Get list_status for this row
            list_status = str(self.df.iloc[index.row()]["list_status"]).lower().strip()
            # Return the text color for this status
            return QBrush(self.status_text_colors.get(list_status, QColor("#FFFFFF")))

        elif role == Qt.TextAlignmentRole:
            # Right-align the hour_limit column
            if self.df.columns[index.column()] == "hour_limit":
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return QVariant()

    def header_data(self, section, orientation, role):
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
            if orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def set_data(self, index, value, role=Qt.EditRole):
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
        """Return item flags for the given index."""
        # Remove ItemIsEditable flag to prevent direct editing
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # Alias Qt method names to maintain compatibility
    rowCount = row_count
    columnCount = column_count
    headerData = header_data
    setData = set_data


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
        self.eightbox_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "eightbox.sqlite"
        )
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

        # Initialize statistics labels and values
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

        # Create statistics panel with Material Design styling and hover effects
        stats_panel = QWidget()
        stats_panel.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 10px;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 13px;
                padding: 4px;
            }
            QLabel[class="stat-value"][status="all"] {
                color: #E1E1E1;
                font-weight: 500;
            }
            QLabel[class="stat-value"][status="otdl"] {
                color: #BB86FC;  /* Purple */
                font-weight: 500;
            }
            QLabel[class="stat-value"][status="wal"] {
                color: #03DAC6;  /* Teal */
                font-weight: 500;
            }
            QLabel[class="stat-value"][status="nl"] {
                color: #64DD17;  /* Light Green */
                font-weight: 500;
            }
            QLabel[class="stat-value"][status="ptf"] {
                color: #FF7597;  /* Pink */
                font-weight: 500;
            }
            QWidget[class="stat-container"] {
                border-radius: 4px;
                padding: 4px 12px;
            }
            QWidget[class="stat-container"]:hover {
                background-color: rgba(103, 80, 164, 0.08);
            }
            QWidget[class="stat-container"][selected="true"] {
                background-color: rgba(103, 80, 164, 0.15);
            }
        """
        )
        stats_layout = QHBoxLayout(stats_panel)
        stats_layout.setSpacing(20)  # Space between stat items
        stats_layout.setContentsMargins(8, 4, 8, 4)  # Tighter margins

        # Add stretch before the stats to push them to center
        stats_layout.addStretch()

        # Create labels for statistics in a more compact layout
        for label_text, value_widget, status in [
            ("ALL", self.total_value, "all"),
            ("OTDL", self.otdl_value, "otdl"),
            ("WAL", self.wal_value, "wal"),
            ("NL", self.nl_value, "nl"),
            ("PTF", self.ptf_value, "ptf"),
        ]:
            stat_container = QWidget()
            stat_container.setProperty("class", "stat-container")
            stat_container.setProperty("selected", False)
            stat_layout = QHBoxLayout(stat_container)
            stat_layout.setContentsMargins(4, 4, 4, 4)
            stat_layout.setSpacing(4)  # Tighter spacing

            label = QLabel(label_text)
            value_widget.setProperty(
                "status", status
            )  # Set the status property for color
            stat_layout.addWidget(label)
            stat_layout.addWidget(value_widget)

            stat_container.status = status
            stat_container.mousePressEvent = lambda e, s=status: self.filter_by_status(
                s
            )
            stats_layout.addWidget(stat_container)
            setattr(self, f"{status}_container", stat_container)

        # Add stretch after the stats to push them to center
        stats_layout.addStretch()
        content_layout.addWidget(stats_panel)

        # Create search bar with Material Design styling
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search carriers...")
        self.filter_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #262626;
                color: #E1E1E1;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px 12px 8px 36px;  /* Added left padding for icon */
                font-size: 13px;
                selection-background-color: #BB86FC;
                selection-color: #000000;
            }
            QLineEdit:focus {
                border: 1px solid #BB86FC;
                background-color: #2D2D2D;
            }
            QLineEdit:hover {
                background-color: #2A2A2A;
            }
        """
        )

        # Create search icon label using Unicode character
        search_icon = QLabel("⚲")  # Unicode search symbol
        search_icon.setStyleSheet(
            """
            QLabel {
                color: #666666;
                font-size: 16px;
                padding: 0px;
                margin: 0px;
            }
            """
        )

        # Add widgets to layout
        search_layout.addWidget(self.filter_input)

        # Set the icon's position absolutely within the search container
        search_icon.setParent(self.filter_input)
        search_icon.move(12, 8)  # Position the icon inside the input field

        content_layout.addWidget(search_container)

        # Add table view with Material Design styling
        self.table_view = QTableView()
        self.table_view.setEditTriggers(
            QTableView.NoEditTriggers
        )  # Disable all editing
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setShowGrid(False)
        self.table_view.setAlternatingRowColors(False)  # Disable alternating row colors
        self.table_view.verticalHeader().setVisible(False)  # Hide row numbers

        # Set the table to stretch to fill the window
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Set specific column widths and alignment
        def setup_table_columns():
            # Set column widths proportionally
            total_width = self.table_view.width()
            self.table_view.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.Interactive
            )  # carrier_name
            self.table_view.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.Interactive
            )  # effective_date
            self.table_view.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.Interactive
            )  # list_status
            self.table_view.horizontalHeader().setSectionResizeMode(
                3, QHeaderView.Interactive
            )  # route_s
            self.table_view.horizontalHeader().setSectionResizeMode(
                4, QHeaderView.Stretch
            )  # hour_limit

            # Set initial column widths
            self.table_view.setColumnWidth(0, int(total_width * 0.25))  # carrier_name
            self.table_view.setColumnWidth(1, int(total_width * 0.20))  # effective_date
            self.table_view.setColumnWidth(2, int(total_width * 0.15))  # list_status
            self.table_view.setColumnWidth(3, int(total_width * 0.20))  # route_s
            # hour_limit will stretch to fill remaining space

            # Right-align the hour_limit column using our custom delegate
            self.table_view.setItemDelegateForColumn(
                4, RightAlignDelegate(self.table_view)
            )

        # Call setup_table_columns after the model is set
        QTimer.singleShot(0, setup_table_columns)

        self.table_view.setStyleSheet(
            """
            QTableView {
                background-color: #1E1E1E;
                alternate-background-color: transparent;
                gridline-color: transparent;
                border: 1px solid #333333;
                border-radius: 4px;
                selection-background-color: #BB86FC;
                selection-color: #000000;
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
                padding: 8px 4px;
                border-bottom: 1px solid rgba(51, 51, 51, 0.5);
            }
            QTableView::item:selected {
                background: #BB86FC;
                color: #000000;
            }
            QTableView::item:hover {
                background-color: rgba(187, 134, 252, 0.1);
            }
            QTableView::item:focus {
                background: #BB86FC;
                color: #000000;
                outline: none;
            }
            QTableView::item:selected:focus {
                background: #BB86FC;
                color: #000000;
                outline: none;
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

        # Create toolbar-style button row
        button_container = QWidget()
        button_container.setStyleSheet(
            """
            QWidget {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 8px;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: 500;
                min-height: 28px;
                min-width: 60px;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #353535;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: rgba(225, 225, 225, 0.3);
            }
            QPushButton#primary {
                background-color: #BB86FC;
                color: #000000;
            }
            QPushButton#primary:hover {
                background-color: #CBB0FF;
            }
            QPushButton#primary:pressed {
                background-color: #9965DA;
            }
            QPushButton#destructive {
                background-color: #CF6679;
                color: #000000;
            }
            QPushButton#destructive:hover {
                background-color: #FF8296;
            }
            QPushButton#destructive:pressed {
                background-color: #B4424F;
            }
            """
        )
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(8, 4, 8, 4)
        button_layout.setSpacing(4)

        # Left-aligned buttons
        left_button_container = QWidget()
        left_button_layout = QHBoxLayout(left_button_container)
        left_button_layout.setContentsMargins(0, 0, 0, 0)
        left_button_layout.setSpacing(4)

        # Create action buttons with consistent sizing
        edit_button = QPushButton("EDIT")
        edit_button.setFixedWidth(60)
        edit_button.clicked.connect(self.edit_carrier)
        left_button_layout.addWidget(edit_button)

        remove_button = QPushButton("REMOVE")
        remove_button.setFixedWidth(60)
        remove_button.setObjectName("destructive")
        remove_button.clicked.connect(self.remove_carrier)
        left_button_layout.addWidget(remove_button)

        # Add Removed Carriers button
        removed_button = QPushButton("REMOVED")
        removed_button.setFixedWidth(60)
        removed_button.clicked.connect(self.show_removed_carriers)
        left_button_layout.addWidget(removed_button)

        button_layout.addWidget(left_button_container)
        button_layout.addStretch()

        # Right-aligned buttons
        right_button_container = QWidget()
        right_button_layout = QHBoxLayout(right_button_container)
        right_button_layout.setContentsMargins(0, 0, 0, 0)
        right_button_layout.setSpacing(4)

        reset_button = QPushButton("RESET")
        reset_button.setFixedWidth(60)
        reset_button.clicked.connect(self.reset_carrier_list)
        right_button_layout.addWidget(reset_button)

        save_button = QPushButton("SAVE")
        save_button.setFixedWidth(60)
        save_button.setObjectName("primary")
        save_button.clicked.connect(self.save_to_json)
        right_button_layout.addWidget(save_button)

        button_layout.addWidget(right_button_container)

        content_layout.addWidget(button_container)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)

        # Set the layout
        self.setLayout(main_layout)

        # Connect filter input
        self.filter_input.textChanged.connect(self.apply_filter)

        # Set minimum size
        self.setMinimumSize(300, 700)

        # Add method to update statistics
        self.update_statistics()

        # Connect model changes to statistics updates
        self.proxy_model.layoutChanged.connect(self.update_statistics)
        self.filter_input.textChanged.connect(self.update_statistics)

        # Create ignored_carriers table if it doesn't exist
        self.create_ignored_carriers_table()

        # Connect our own signal to refresh the view
        self.carrier_list_updated.connect(self.refresh_carrier_list)

    def minimize_to_button(self):
        """Custom minimize handler that properly hides the window"""
        if self.parent_main and hasattr(self.parent_main, "carrier_list_button"):
            self.parent_main.carrier_list_button.setChecked(False)
        self.hide()

    def change_event(self, event):
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

    def hide_event(self, event):
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

    def init_ui(self, layout):
        """Initialize the user interface components.

        Sets up the table view, filter input, and control buttons
        for the carrier list tab.

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
                and parent.date_selection_pane.selected_range is not None
            ):
                # Only emit signals if we have a valid date range
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
            "hour_limit": float,
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
        df["hour_limit"] = df["hour_limit"].fillna(12.00)  # Default to 12.00 hours

        # Convert any 0.0 hour limits to 12.00
        df.loc[df["hour_limit"] == 0.0, "hour_limit"] = 12.00

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
        # Filter out ignored carriers
        ignored_carriers = self.get_ignored_carriers()
        new_carrier_names = [
            name for name in new_carrier_names if name not in ignored_carriers
        ]

        if not new_carrier_names:
            return

        # Show custom dialog and get selected carriers
        selected_carriers, carriers_to_ignore = NewCarriersDialog.get_new_carriers(
            self.parent_widget, new_carrier_names
        )

        # Add selected carriers to ignored list
        if carriers_to_ignore:
            self.add_to_ignored_carriers(carriers_to_ignore)

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
                    and self.parent_widget.date_selection_pane.selected_range
                    is not None
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

        # Create an edit dialog with frameless window hint
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout with no margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        title_bar = CustomTitleBarWidget(title="Edit Carrier", parent=dialog)
        main_layout.addWidget(title_bar)

        # Create content widget with Material Design styling
        content_widget = QWidget()
        content_widget.setStyleSheet(
            f"""
            QWidget {{
                background-color: {MATERIAL_BACKGROUND.name()};
                color: {COLOR_TEXT_LIGHT.name()};
            }}
            QLabel {{
                color: {COLOR_TEXT_LIGHT.name()};
                font-size: 13px;
                font-weight: bold;
                padding: 4px;
                margin-top: 8px;
            }}
            QLineEdit {{
                background-color: {MATERIAL_SURFACE.name()};
                color: {COLOR_TEXT_LIGHT.name()};
                border: 2px solid {COLOR_TEXT_DIM.name()};
                border-radius: 4px;
                padding: 12px;
                margin: 4px 0px 12px 0px;
                font-size: 14px;
            }}
            QLineEdit:disabled {{
                background-color: {MATERIAL_BACKGROUND.name()};
                color: {COLOR_TEXT_DIM.name()};
                border: 1px solid {COLOR_TEXT_DIM.name()};
            }}
            QComboBox {{
                background-color: {MATERIAL_SURFACE.name()};
                color: {COLOR_TEXT_LIGHT.name()};
                border: 2px solid {COLOR_TEXT_DIM.name()};
                border-radius: 4px;
                padding: 12px;
                padding-right: 36px;
                margin: 4px 0px 12px 0px;
                font-size: 14px;
                min-width: 200px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 36px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {MATERIAL_PRIMARY.name()};
                width: 10px;
                height: 10px;
                margin-right: 12px;
            }}
            QComboBox:hover {{
                border-color: {MATERIAL_PRIMARY.name()};
            }}
            QComboBox:focus {{
                border: 2px solid {MATERIAL_PRIMARY.name()};
            }}
            QComboBox QAbstractItemView {{
                background-color: {MATERIAL_SURFACE.name()};
                color: {COLOR_TEXT_LIGHT.name()};
                selection-background-color: {MATERIAL_PRIMARY.name()};
                selection-color: black;
                border: 1px solid {COLOR_TEXT_DIM.name()};
                padding: 4px;
            }}
            QPushButton {{
                background-color: {MATERIAL_SURFACE.name()};
                color: {MATERIAL_PRIMARY.name()};
                border: 2px solid {MATERIAL_PRIMARY.name()};
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                min-width: 120px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(187, 134, 252, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(187, 134, 252, 0.2);
            }}
            QPushButton#primary {{
                background-color: {MATERIAL_PRIMARY.name()};
                color: black;
                border: none;
            }}
            QPushButton#primary:hover {{
                background-color: {MATERIAL_PRIMARY.lighter(110).name()};
            }}
            QPushButton#primary:pressed {{
                background-color: {MATERIAL_PRIMARY.darker(110).name()};
            }}
            """
        )

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(8)

        # Add a title label
        title_label = QLabel(f"Editing Carrier: {carrier_data['carrier_name']}")
        title_label.setStyleSheet(
            f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLOR_TEXT_LIGHT.name()};
            padding: 0px 0px 16px 0px;
            """
        )
        content_layout.addWidget(title_label)

        # Carrier name input with icon
        name_label = QLabel("Carrier Name")
        name_input = QLineEdit(carrier_data["carrier_name"])
        name_input.setReadOnly(True)
        content_layout.addWidget(name_label)
        content_layout.addWidget(name_input)

        # List status dropdown with icon
        list_status_label = QLabel("List Status")
        list_status_dropdown = QComboBox()
        list_status_dropdown.addItems(["otdl", "ptf", "wal", "nl"])
        list_status_dropdown.setCurrentText(carrier_data["list_status"])
        content_layout.addWidget(list_status_label)
        content_layout.addWidget(list_status_dropdown)

        # Hour limit dropdown with icon
        hour_limit_label = QLabel("Hour Limit")
        hour_limit_dropdown = QComboBox()
        content_layout.addWidget(hour_limit_label)
        content_layout.addWidget(hour_limit_dropdown)

        # Populate the hour_limit_dropdown based on initial list_status
        def update_hour_limit_options():
            hour_limit_dropdown.clear()
            if list_status_dropdown.currentText().lower() == "otdl":
                hour_limit_dropdown.addItems(["12.00", "11.00", "10.00"])
            else:
                hour_limit_dropdown.addItems(["12.00", "11.00", "10.00", "(none)"])

        update_hour_limit_options()
        list_status_dropdown.currentTextChanged.connect(update_hour_limit_options)

        # Set current hour limit
        current_hour_limit = carrier_data["hour_limit"]
        if current_hour_limit is not None:
            try:
                current_hour_limit = f"{float(current_hour_limit):.2f}"
            except (ValueError, TypeError):
                current_hour_limit = "(none)"
        else:
            current_hour_limit = "(none)"

        if current_hour_limit in [
            hour_limit_dropdown.itemText(i) for i in range(hour_limit_dropdown.count())
        ]:
            hour_limit_dropdown.setCurrentText(current_hour_limit)
        else:
            hour_limit_dropdown.setCurrentText("(none)")

        # Add spacing before buttons
        content_layout.addSpacing(16)

        # Create button container with horizontal layout
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(16)
        button_layout.addStretch()

        # Create OK and Cancel buttons
        ok_button = QPushButton("Save")
        ok_button.setObjectName("primary")
        cancel_button = QPushButton("Cancel")

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        content_layout.addWidget(button_container)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        dialog.setLayout(main_layout)

        # Set minimum size and center on parent
        dialog.setMinimumSize(400, 500)
        if self.parent():
            dialog.move(
                self.parent().x() + (self.parent().width() - dialog.width()) // 2,
                self.parent().y() + (self.parent().height() - dialog.height()) // 2,
            )

        # Handle dialog actions
        def on_accept():
            # Update the DataFrame with new values
            new_list_status = list_status_dropdown.currentText()
            selected_hour_limit = hour_limit_dropdown.currentText()
            self.main_model.df.loc[sorted_df_index, "list_status"] = new_list_status
            self.main_model.df.loc[sorted_df_index, "hour_limit"] = (
                None if selected_hour_limit == "(none)" else float(selected_hour_limit)
            )

            # Refresh the proxy model
            self.main_model.update_data(self.main_model.df)
            self.proxy_model.invalidate()  # Ensure the proxy model refreshes
            dialog.accept()

        ok_button.clicked.connect(on_accept)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def remove_carrier(self):
        """Remove the selected carrier from the list.

        Shows confirmation dialog before removal. Updates the model,
        JSON file, and emits appropriate signals after successful removal.
        Also adds the removed carrier to the ignored list.
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
                f"Are you sure you want to remove carrier '{carrier_name}'?\n\n"
                "The carrier will be added to the removed list\n\n"
                "and won't appear in violation detection.",
                self,
            )
            if confirm_dialog.exec_() == QDialog.Accepted:
                # Add carrier to ignored list
                self.add_to_ignored_carriers([carrier_name])

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
                    self,
                    "Success",
                    f"Carrier '{carrier_name}' removed successfully and added to ignored list.",
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

                # Add hour_limit column with default value of 12.00
                if "hour_limit" not in df.columns:
                    df["hour_limit"] = 12.00

                return df

        except Exception as e:
            CustomNotificationDialog.show_notification(self, "Database Error", str(e))
            return pd.DataFrame(
                columns=[
                    "carrier_name",
                    "effective_date",
                    "list_status",
                    "route_s",
                    "hour_limit",
                ]
            ).assign(
                hour_limit=12.00
            )  # Set default hour_limit in empty DataFrame too

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

    def has_valid_date_range(self):
        """Check if a valid date range is selected.

        Returns:
            bool: True if a valid date range is selected, False otherwise
        """
        return (
            hasattr(self.parent_widget, "date_selection_pane")
            and self.parent_widget.date_selection_pane is not None
            and hasattr(self.parent_widget.date_selection_pane, "selected_range")
            and self.parent_widget.date_selection_pane.selected_range is not None
        )

    def reset_carrier_list(self):
        """Reset the carrier list to its initial state.

        Deletes the carrier list JSON file and reloads carrier data from the database.
        Shows confirmation dialog before proceeding and notification after completion.
        """
        # Show confirmation dialog
        confirm_dialog = ConfirmDialog(
            "Are you sure you want to reset the carrier list?\n\n"
            "This will remove all customizations and reload carriers from the database.",
            self,
        )
        if confirm_dialog.exec_() == QDialog.Accepted:
            try:
                # Delete the JSON file if it exists
                if os.path.exists(self.json_path):
                    os.remove(self.json_path)

                # Reload carrier data from database
                df = self.fetch_carrier_data()

                # Update the model with the new data
                self.main_model.update_data(df)

                # Emit signals to update the main application
                self.carrier_list_updated.emit(df)
                self.data_updated.emit(df)

                # If we have a valid date selected, trigger a refresh
                if (
                    hasattr(self.parent_widget, "date_selection_pane")
                    and self.parent_widget.date_selection_pane is not None
                    and self.parent_widget.date_selection_pane.selected_range
                    is not None
                ):
                    self.request_apply_date_range.emit()

                CustomNotificationDialog.show_notification(
                    self, "Success", "Carrier list has been reset to its initial state."
                )

                # Update statistics
                self.update_statistics()

            except Exception as e:
                CustomErrorDialog.error(
                    self, "Error", f"Failed to reset carrier list: {e}"
                )

    def hideEvent(self, event):
        """Handle hide event by unchecking the corresponding button."""
        if hasattr(self.parent_main, "carrier_list_button"):
            self.parent_main.carrier_list_button.setChecked(False)
        super().hideEvent(event)

    def create_ignored_carriers_table(self):
        """Create the ignored_carriers table if it doesn't exist."""
        try:
            with sqlite3.connect(self.eightbox_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ignored_carriers (
                        carrier_name varchar PRIMARY KEY,
                        ignored_date datetime DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                conn.commit()
        except Exception as e:
            CustomErrorDialog.error(
                self, "Database Error", f"Failed to create ignored carriers table: {e}"
            )

    def get_ignored_carriers(self):
        """Get list of carriers that have been marked as ignored."""
        try:
            with sqlite3.connect(self.eightbox_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT carrier_name FROM ignored_carriers")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            CustomErrorDialog.error(
                self, "Database Error", f"Failed to fetch ignored carriers: {e}"
            )
            return []

    def add_to_ignored_carriers(self, carriers):
        """Add carriers to the ignored list.

        Args:
            carriers (list): List of carrier names to ignore
        """
        if not carriers:
            return

        try:
            with sqlite3.connect(self.eightbox_db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT OR REPLACE INTO ignored_carriers (carrier_name) VALUES (?)",
                    [(carrier,) for carrier in carriers],
                )
                conn.commit()
        except Exception as e:
            CustomErrorDialog.error(
                self, "Database Error", f"Failed to add carriers to ignore list: {e}"
            )

    def show_removed_carriers(self):
        """Show the removed carriers manager dialog."""
        from removed_carriers_manager import RemovedCarriersManager

        dialog = RemovedCarriersManager(self.eightbox_db_path, self)
        dialog.exec_()

    def refresh_carrier_list(self, updated_df=None):
        """Refresh the carrier list view with updated data.

        Args:
            updated_df (pd.DataFrame, optional): Updated carrier data. If None,
                reloads from the JSON file.
        """
        try:
            if updated_df is None:
                # Reload from JSON file
                updated_df = pd.read_json(self.json_path, orient="records")

            # Sort the DataFrame
            status_order = ["nl", "wal", "otdl", "ptf"]
            updated_df["list_status"] = pd.Categorical(
                updated_df["list_status"], categories=status_order, ordered=True
            )
            updated_df = updated_df.sort_values(
                ["list_status", "carrier_name"], ascending=[True, True]
            ).reset_index(drop=True)

            # Update the model
            self.carrier_df = updated_df
            self.main_model.update_data(updated_df)
            self.proxy_model.invalidate()

            # Update statistics
            self.update_statistics()

        except Exception as e:
            CustomWarningDialog.warning(
                self, "Refresh Error", f"Failed to refresh carrier list: {e}"
            )
