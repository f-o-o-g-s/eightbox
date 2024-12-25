"""Main graphical user interface for the application.

Implements the primary window and core UI functionality, coordinating between
different panes and managing the overall application state and user interactions.
"""

import json
import os
import sys

import pandas as pd  # Data manipulation
from PyQt5.QtCore import (
    QRect,
    Qt,
    QTimer,
    qInstallMessageHandler,
)
from PyQt5.QtWidgets import (  # Specific widget import for header configuration
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from carrier_list_pane import CarrierListPane
from clean_moves_dialog import CleanMovesDialog
from clean_moves_utils import (
    detect_invalid_moves,
    get_valid_routes,
)
from custom_widgets import (
    CustomInfoDialog,
    CustomProgressDialog,
    CustomSizeGrip,
    CustomWarningDialog,
)
from database.initializer import DatabaseInitializer
from database.models import ClockRingQueryParams
from database.path_manager import DatabasePathManager
from database.service import DatabaseService
from date_selection_pane import DateSelectionPane
from excel_export import ExcelExporter
from otdl_maximization_pane import OTDLMaximizationPane
from settings_dialog import SettingsDialog
from tabs.violations import (
    Violation85dTab,
    Violation85f5thTab,
    Violation85fNsTab,
    Violation85fTab,
    Violation85gTab,
    ViolationMax12Tab,
    ViolationMax60Tab,
    ViolationRemediesTab,
)
from theme import apply_material_dark_theme
from violation_detection import (
    detect_violations,
    get_violation_remedies,
)

VERSION = "2024.1.2.3"  # Updated by release.py
BUILD_TIME = "2024-12-25 14:16"  # Updated by release.py


def qt_message_handler(mode, context, message):
    """Handle Qt debug/warning messages.

    Custom message handler that filters out specific Qt warnings while
    passing through other messages to the console.

    Args:
        mode: Message type/severity
        context: Context information about the message
        message (str): The actual message content
    """
    if "Unknown property cursor" not in message:  # Ignore cursor property warnings
        print(mode, context, message)


qInstallMessageHandler(qt_message_handler)


class CustomTitleBar(QWidget):
    """Custom window title bar with minimize/maximize/close controls.

    Implements a draggable title bar with:
    - Application title and branding
    - Window control buttons (minimize, maximize/restore, close)
    - Custom styling and hover effects
    - Double-click maximize/restore functionality
    - Window dragging support

    Attributes:
        parent (QWidget): Parent window containing this title bar
        title (QLabel): Label displaying the application name
        dragPos: Position tracking for window dragging
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)

        # Set background color for the entire title bar
        self.setStyleSheet(
            """
            QWidget {
                background-color: #37474F;
                border: none;
            }
            QLabel {
                color: white;
                font-size: 12pt;
                font-weight: bold;
                background-color: transparent;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                padding: 5px;
                min-width: 40px;
                max-width: 40px;
                font-size: 16pt;
                font-family: Arial;
            }
            QPushButton:hover { background-color: #455A64; }
        """
        )

        layout = QHBoxLayout()
        # Remove all margins to extend background to edges
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title label with left padding
        self.title = QLabel(
            "  Eightbox - Branch 815 - Violation Detection"
        )  # Added spaces for left padding
        layout.addWidget(self.title)
        layout.addStretch()

        # Create a container for window controls
        window_controls = QWidget()
        window_controls_layout = QHBoxLayout()
        window_controls_layout.setContentsMargins(0, 0, 0, 0)
        window_controls_layout.setSpacing(0)

        minimize_btn = QPushButton("─")
        minimize_btn.clicked.connect(self.parent.showMinimized)

        maximize_btn = QPushButton("□")
        maximize_btn.clicked.connect(self.toggle_maximize)

        close_btn = QPushButton("×")
        close_btn.setStyleSheet("QPushButton:hover { background-color: #c42b1c; }")
        close_btn.clicked.connect(self.parent.close)

        window_controls_layout.addWidget(minimize_btn)
        window_controls_layout.addWidget(maximize_btn)
        window_controls_layout.addWidget(close_btn)
        window_controls.setLayout(window_controls_layout)

        layout.addWidget(window_controls)
        self.setLayout(layout)

    def toggle_maximize(self):
        """Toggle between maximized and normal window state."""
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging.

        Captures the initial position when the user clicks on the window,
        enabling window dragging functionality.

        Args:
            event (QMouseEvent): The mouse press event containing position data
        """
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging.

        Updates the window position as the user drags, creating a smooth
        window movement effect.

        Args:
            event (QMouseEvent): The mouse move event containing position data
        """
        if event.buttons() == Qt.LeftButton and self.dragPos is not None:
            delta = event.globalPos() - self.dragPos
            self.parent.move(self.parent.pos() + delta)
            self.dragPos = event.globalPos()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click events for window maximization.

        Toggles between maximized and normal window state when the user
        double-clicks on the window.

        Args:
            event (QMouseEvent): The mouse double-click event
        """
        self.toggle_maximize()


class MainApp(QMainWindow):
    """Main application window.

    Implements the primary application window and coordinates all major components.
    Manages the overall application state and user interactions.

    Class Attributes:
        VERSION (str): Current version in YYYY.MAJOR.MINOR.PATCH format
        BUILD_TIME (str): Build timestamp in YYYY-MM-DD HH:MM format

    Attributes:
        current_data (pd.DataFrame): Currently loaded clock ring data
        violations (dict): Detected violations organized by type
        vio_85d_tab (Violation85dTab): Tab for 8.5.D violations
        vio_85f_tab (Violation85fTab): Tab for 8.5.F violations
        vio_85f_ns_tab (Violation85fNsTab): Tab for non-scheduled day violations
        vio_85f_5th_tab (Violation85f5thTab): Tab for fifth occurrence violations
        vio_85g_tab (Violation85gTab): Tab for 8.5.G violations
        vio_MAX12_tab (ViolationMax12Tab): Tab for 12-hour limit violations
        vio_MAX60_tab (ViolationMax60Tab): Tab for 60-hour limit violations
        remedies_tab (ViolationRemediesTab): Summary tab for all violations
        carrier_list_pane (CarrierListPane): Carrier management interface
        otdl_maximization_pane (OTDLMaximizationPane): OTDL assignment interface
    """

    VERSION = "2024.1.3.0"  # Updated by release.py
    BUILD_TIME = "2024-12-25 14:11"  # Updated by release.py

    def __init__(self):
        super().__init__()

        # Initialize window properties
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setMinimumSize(800, 600)

        # Initialize database path manager first
        self.path_manager = DatabasePathManager()

        # Load database path with fallback behavior
        self.mandates_db_path = self.path_manager.load_database_path()

        # Set eightbox database path
        self.eightbox_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "eightbox.sqlite"
        )

        # Initialize database service
        self.db_service = DatabaseService()

        # Initialize window attributes and UI components
        self._init_window_attributes()
        self._init_ui_components()

        # Initialize database
        self._init_database()

        # Show database configuration dialog only if path is not found
        if not self.mandates_db_path:
            self.open_settings_dialog()

    def _init_window_attributes(self):
        """Initialize window-specific attributes."""
        # Add resize attributes
        self._resizing = False
        self._resize_edge = None
        self._last_edge = None
        self.MARGINS = 10

        # Set mouse tracking to ensure we get all mouse move events
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)

        # Create a transparent widget to handle resize events
        self._resize_frame = QWidget(self)
        self._resize_frame.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._resize_frame.setStyleSheet("background: transparent;")
        self._resize_frame.setMouseTracking(True)

        # Install event filter on the main window
        self.installEventFilter(self)

    def _init_ui_components(self):
        """Initialize all UI components."""
        # Apply material dark theme
        apply_material_dark_theme(QApplication.instance())

        # Set initial window geometry
        self.setWindowTitle("Eightbox - Branch 815 - Violation Detection")
        self.setGeometry(100, 100, 1200, 800)

        # Hide status bar
        self.statusBar().hide()

        # Track active progress dialogs
        self.active_progress_dialogs = []

        # Create the excel exporter first
        self.excel_exporter = ExcelExporter(self)

        # Track current filter state
        self.current_status_filter = "all"

        # Initialize UI components in correct order
        self._init_title_bar()  # Initialize title bar first
        self._init_container()  # Then container which uses title bar
        self._init_menu_content()
        self._init_tabs()
        self._init_size_grip()

    def _init_database(self):
        """Initialize the database with proper error handling."""
        if not self.initialize_eightbox_database(self.mandates_db_path):
            CustomWarningDialog.warning(
                self,
                "Database Error",
                "Failed to initialize the working database.\n"
                "Please check the application logs for details.",
            )

    def setup_ui(self):
        """Set up the user interface."""
        self.init_window_properties()
        self.init_layouts()
        self.init_widgets()
        self.init_connections()

    def _get_resize_edge(self, pos):
        """Determine which edge to resize based on mouse position."""
        margin = self.MARGINS
        width = self.width()
        height = self.height()

        x = pos.x()
        y = pos.y()

        # Skip edge detection if we're over certain widgets
        child = self.childAt(pos)
        if child and isinstance(child, (QMenuBar, CustomTitleBar)):
            return None

        # Define regions
        left_edge = x <= margin
        right_edge = x >= width - margin
        bottom_edge = y >= height - margin

        # Check bottom corners first
        if left_edge and bottom_edge:
            return "bottomleft"
        if right_edge and bottom_edge:
            return "bottomright"

        # Then check edges
        if left_edge:
            return "left"
        if right_edge:
            return "right"
        if bottom_edge:
            return "bottom"

        return None

    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing and cursor updates."""
        if self._resizing and self._resize_edge:
            # Handle resizing
            delta = event.globalPos() - self._resize_start_pos
            new_geometry = QRect(self._resize_start_geometry)

            if self._resize_edge == "right":
                new_geometry.setRight(new_geometry.right() + delta.x())
            elif self._resize_edge == "bottom":
                new_geometry.setBottom(new_geometry.bottom() + delta.y())
            elif self._resize_edge == "left":
                new_geometry.setLeft(new_geometry.left() + delta.x())
            elif self._resize_edge == "bottomleft":
                new_geometry.setBottomLeft(new_geometry.bottomLeft() + delta)
            elif self._resize_edge == "bottomright":
                new_geometry.setBottomRight(new_geometry.bottomRight() + delta)

            new_size = new_geometry.size()
            new_size = new_size.expandedTo(self.minimumSize())
            new_geometry.setSize(new_size)

            self.setGeometry(new_geometry)
            event.accept()
            return

        # Handle cursor updates
        edge = self._get_resize_edge(event.pos())

        # Always update cursor based on position
        if edge:
            if edge in ("left", "right"):
                QApplication.changeOverrideCursor(Qt.SizeHorCursor)
            elif edge == "bottom":
                QApplication.changeOverrideCursor(Qt.SizeVerCursor)
            elif edge == "bottomleft":
                QApplication.changeOverrideCursor(Qt.SizeBDiagCursor)
            elif edge == "bottomright":
                QApplication.changeOverrideCursor(Qt.SizeFDiagCursor)
            event.accept()
        else:
            QApplication.restoreOverrideCursor()
            event.ignore()
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press for resizing."""
        if event.button() == Qt.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        event.ignore()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release for resizing."""
        was_resizing = self._resizing
        if was_resizing:
            self._resizing = False
            self._resize_edge = None

            # Update cursor based on current position
            edge = self._get_resize_edge(event.pos())
            if edge:
                if edge in ("left", "right"):
                    QApplication.changeOverrideCursor(Qt.SizeHorCursor)
                elif edge == "bottom":
                    QApplication.changeOverrideCursor(Qt.SizeVerCursor)
                elif edge == "bottomleft":
                    QApplication.changeOverrideCursor(Qt.SizeBDiagCursor)
                elif edge == "bottomright":
                    QApplication.changeOverrideCursor(Qt.SizeFDiagCursor)
            else:
                QApplication.restoreOverrideCursor()
            event.accept()
        else:
            event.ignore()
            super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        """Reset cursor when mouse leaves the window."""
        QApplication.restoreOverrideCursor()
        self._resizing = False
        self._resize_edge = None
        super().leaveEvent(event)

    def enterEvent(self, event):
        """Reset cursor state when mouse enters the window."""
        QApplication.restoreOverrideCursor()
        self._resizing = False
        self._resize_edge = None
        super().enterEvent(event)

    def handle_main_tab_change(self, index):
        """Handle switching between main violation tabs.

        Maintains the current filter state across tab switches.

        Args:
            index (int): Index of the newly selected tab
        """
        # Get the current tab
        current_tab = self.central_tab_widget.widget(index)

        # If we have a valid tab and current filter state
        if current_tab and hasattr(current_tab, "filter_carriers"):
            # Apply filters in the correct order

            # 1. Apply carrier name filter if it exists
            if hasattr(self, "carrier_filter"):
                filter_text = self.carrier_filter.text()
                if filter_text:
                    current_tab.current_filter = filter_text
                    current_tab.current_filter_type = "name"
                    current_tab.filter_carriers(
                        filter_text, filter_type="name"
                    )  # Split to fix line length

            # 2. Apply status filter if it exists
            if (
                hasattr(self, "current_status_filter")
                and self.current_status_filter != "all"
            ):
                if hasattr(current_tab, "handle_global_filter_click"):
                    current_tab.handle_global_filter_click(self.current_status_filter)

            # 3. Update stats
            if hasattr(current_tab, "update_stats"):
                current_tab.update_stats()

    def init_top_button_row(self):
        """Create a horizontal row for utility buttons
        (Date Selection, Carrier List, OTDL Maximization)"""
        # Create button row layout
        button_row_layout = QHBoxLayout()
        button_row_layout.setContentsMargins(8, 8, 8, 8)

        # Create a container widget for the button row with a darker background
        button_container = QWidget()
        button_container.setStyleSheet(
            """
            QWidget {
                background-color: #121212;  /* Material Dark background */
                border-bottom: 1px solid #2D2D2D;
            }
            QPushButton {
                background-color: rgba(187, 134, 252, 0.05);  /* Primary color with 5% opacity */
                border: none;
                border-radius: 4px;
                color: #BB86FC;  /* Primary color */
                padding: 16px 32px;  /* Increased padding */
                font-size: 14px;  /* Increased font size */
                font-weight: 500;
                text-align: center;
                margin: 12px 6px;  /* Increased margins */
                min-width: 180px;  /* Increased width */
                letter-spacing: 0.15px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: rgba(187, 134, 252, 0.08);
                color: #CBB0FF;
            }
            QPushButton:pressed {
                background-color: rgba(187, 134, 252, 0.12);
                padding-top: 17px;
                color: #BB86FC;
            }
            QPushButton:checked {
                background-color: rgba(187, 134, 252, 0.12);
                color: #E9B7FF;
                font-weight: 600;
            }
            QPushButton:checked:hover {
                background-color: rgba(187, 134, 252, 0.16);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.12);
                color: rgba(255, 255, 255, 0.38);
            }
            """
        )

        # Create buttons with icons
        self.date_selection_button = QPushButton("Date Selection")
        self.date_selection_button.setCheckable(True)
        self.date_selection_button.clicked.connect(self.toggle_date_selection_pane)

        self.carrier_list_button = QPushButton("Carrier List")
        self.carrier_list_button.setCheckable(True)
        self.carrier_list_button.clicked.connect(self.toggle_carrier_list_pane)

        self.otdl_maximization_button = QPushButton("OTDL Maximization")
        self.otdl_maximization_button.setCheckable(True)
        self.otdl_maximization_button.clicked.connect(
            self.toggle_otdl_maximization_pane
        )

        # Add buttons to layout
        button_row_layout.addWidget(self.date_selection_button)
        button_row_layout.addWidget(self.carrier_list_button)
        button_row_layout.addWidget(self.otdl_maximization_button)
        button_row_layout.addStretch()

        button_container.setLayout(button_row_layout)
        self.main_layout.addWidget(button_container)

    def init_filter_row(self):
        """Create a row for the carrier filter textbox."""
        # Create filter row container
        filter_container = QWidget()
        filter_container.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                border-bottom: 1px solid #333333;
            }
            QLineEdit {
                background-color: #2D2D2D;
                color: #E1E1E1;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                margin: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
            QLineEdit::placeholder {
                color: #808080;
            }
            """
        )

        # Create layout for the filter row
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(8, 4, 8, 4)

        # Create and add the filter textbox
        self.carrier_filter = QLineEdit()
        self.carrier_filter.setPlaceholderText("Filter carriers across all tabs...")
        self.carrier_filter.textChanged.connect(self.on_carrier_filter_changed)
        filter_layout.addWidget(self.carrier_filter)

        filter_container.setLayout(filter_layout)
        return filter_container

    def _init_menu_content(self):
        """Initialize the menu content area."""
        # Setup main menu and toolbar
        self.init_menu_toolbar()
        self.menu_content_layout.addWidget(self.menuBar())

        # Create main layout for buttons and central tab widget
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Initialize button row and add to layout
        self.init_top_button_row()

        # Create and add central tab widget
        self.central_tab_widget = QTabWidget()
        self.central_tab_widget.setObjectName("centralTabs")
        self.main_layout.addWidget(self.central_tab_widget)

        # Add the filter row between central tab widget and violation tabs
        self.main_layout.addWidget(self.init_filter_row())

        # Initialize and add bottom filter row
        self.init_filter_button_row()

        # Add main layout to menu content
        self.menu_content_layout.addLayout(self.main_layout)

    def init_filter_button_row(self):
        """Create a horizontal row for filter buttons at the bottom."""
        # Create filter row
        filter_row = QWidget()
        filter_row.setStyleSheet(
            """
            QWidget {
                background-color: #121212;
                border-top: 1px solid #333333;
            }
            QPushButton {
                background-color: rgba(187, 134, 252, 0.05);
                border: none;
                color: rgba(187, 134, 252, 0.87);
                padding: 4px 12px;
                font-size: 12px;
                margin: 1px;
                min-width: 90px;
                max-height: 24px;
                border-radius: 4px;
                text-align: center;
                font-weight: 500;
                letter-spacing: 0.15px;
            }
            QPushButton:hover {
                background-color: rgba(187, 134, 252, 0.08);
                color: rgba(187, 134, 252, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(187, 134, 252, 0.12);
                color: rgba(187, 134, 252, 1.0);
            }
            QPushButton:checked {
                background-color: rgba(187, 134, 252, 0.12);
                color: rgba(187, 134, 252, 1.0);
                font-weight: 600;
            }
            QLabel {
                color: rgba(187, 134, 252, 0.87);
                font-size: 12px;
                padding: 4px 12px;
                background-color: rgba(187, 134, 252, 0.05);
                border-radius: 4px;
                font-weight: 500;
                letter-spacing: 0.15px;
            }
        """
        )

        # Create main filter layout
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(8, 12, 8, 12)
        filter_layout.setSpacing(4)

        # Create status filter buttons with stats
        self.total_btn = self.create_filter_button("All Carriers")
        self.wal_btn = self.create_filter_button("WAL")
        self.nl_btn = self.create_filter_button("NL")
        self.otdl_btn = self.create_filter_button("OTDL")
        self.ptf_btn = self.create_filter_button("PTF")
        self.violations_btn = self.create_filter_button("Carriers With Violations")

        # Add buttons to layout
        for btn in [
            self.total_btn,
            self.wal_btn,
            self.nl_btn,
            self.otdl_btn,
            self.ptf_btn,
            self.violations_btn,
        ]:
            filter_layout.addWidget(btn)

        # Add date range label
        self.date_range_label = QLabel("Selected Date Range: None")
        self.date_range_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        filter_layout.addStretch()
        filter_layout.addWidget(self.date_range_label)

        filter_row.setLayout(filter_layout)
        self.main_layout.addWidget(filter_row)

    def create_filter_button(self, text):
        """Create a styled filter button for list status filtering."""
        btn = QPushButton(text)
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

        # Determine which filter to apply
        if not sender.isChecked():
            self.apply_global_status_filter("all")
        elif sender == self.total_btn:
            self.apply_global_status_filter("all")
        elif sender == self.wal_btn:
            self.apply_global_status_filter("wal")
        elif sender == self.nl_btn:
            self.apply_global_status_filter("nl")
        elif sender == self.otdl_btn:
            self.apply_global_status_filter("otdl")
        elif sender == self.ptf_btn:
            self.apply_global_status_filter("ptf")
        elif sender == self.violations_btn:
            self.apply_global_status_filter("violations")

    def update_filter_stats(self, total, wal, nl, otdl, ptf, violations):
        """Update internal stats without modifying button text."""
        # Store stats internally if needed but don't update button text
        pass

    def apply_global_status_filter(self, status):
        """Apply the global status filter to all tabs."""
        # Store current filter state
        self.current_status_filter = status

        # Get the current active tab
        current_tab = self.central_tab_widget.currentWidget()

        # Apply filter to each violation tab
        for tab in [
            self.vio_85d_tab,
            self.vio_85f_tab,
            self.vio_85f_ns_tab,
            self.vio_85f_5th_tab,
            self.vio_85g_tab,
            self.vio_MAX12_tab,
            self.vio_MAX60_tab,
            self.remedies_tab,
        ]:
            if hasattr(tab, "filter_carriers"):
                if status == "violations":
                    tab.filter_carriers("", filter_type="violations")
                elif status == "all":
                    tab.filter_carriers("")
                else:
                    tab.filter_carriers(status, filter_type="list_status")

                # Only update stats for the currently visible tab
                if tab == current_tab:
                    tab.update_stats()

    def init_85d_tab(self):
        """Initialize the Article 8.5.D violation tab."""
        self.vio_85d_tab = Violation85dTab()
        self.central_tab_widget.addTab(self.vio_85d_tab, "8.5.D")
        self.central_tab_widget.setTabToolTip(0, "8.5.D Violations")
        self.vio_85d_tab.refresh_data(pd.DataFrame())  # Start with an empty DataFrame

    def init_85f_tab(self):
        """Initialize the Article 8.5.F violation tab."""
        self.vio_85f_tab = Violation85fTab()
        self.central_tab_widget.addTab(self.vio_85f_tab, "8.5.F")
        self.central_tab_widget.setTabToolTip(1, "8.5.F Violations")
        self.vio_85f_tab.initUI(pd.DataFrame())  # Start with an empty DataFrame

    def init_85f_ns_tab(self):
        """Initialize the Article 8.5.F non-scheduled day violation tab."""
        self.vio_85f_ns_tab = Violation85fNsTab()
        self.central_tab_widget.addTab(self.vio_85f_ns_tab, "8.5.F NS")
        self.central_tab_widget.setTabToolTip(2, "8.5.F Non-Scheduled Day Violations")
        self.vio_85f_ns_tab.initUI(pd.DataFrame())  # Start with an empty DataFrame

    def init_85f_5th_tab(self):
        """Initialize the Article 8.5.F fifth overtime day violation tab."""
        self.vio_85f_5th_tab = Violation85f5thTab()
        self.central_tab_widget.addTab(self.vio_85f_5th_tab, "8.5.F 5th")
        self.central_tab_widget.setTabToolTip(3, "8.5.F Fifth Day Violations")
        self.vio_85f_5th_tab.refresh_data(
            pd.DataFrame()
        )  # Start with an empty DataFrame

    def init_85g_tab(self):
        """Initialize the Article 8.5.G violation tab."""
        self.vio_85g_tab = Violation85gTab()
        self.central_tab_widget.addTab(self.vio_85g_tab, "8.5.G")
        self.central_tab_widget.setTabToolTip(4, "8.5.G Violations")
        self.vio_85g_tab.refresh_data(pd.DataFrame())  # Start with an empty DataFrame

    def init_MAX12_tab(self):
        """Initialize the Maximum 12-Hour Rule violation tab."""
        self.vio_MAX12_tab = ViolationMax12Tab(self)
        self.central_tab_widget.addTab(self.vio_MAX12_tab, "MAX12")
        self.central_tab_widget.setTabToolTip(5, "Maximum 12-Hour Rule Violations")

    def init_MAX60_tab(self):
        """Initialize the Maximum 60-Hour Rule violation tab."""
        self.vio_MAX60_tab = ViolationMax60Tab(self)
        self.central_tab_widget.addTab(self.vio_MAX60_tab, "MAX60")
        self.central_tab_widget.setTabToolTip(6, "Maximum 60-Hour Rule Violations")

    def init_remedies_tab(self):
        """Initialize the violation remedies summary tab."""
        self.remedies_tab = ViolationRemediesTab()
        self.central_tab_widget.addTab(self.remedies_tab, "Summary")
        self.central_tab_widget.setTabToolTip(7, "Violations Summary")
        self.remedies_tab.refresh_data(pd.DataFrame())  # Start with an empty DataFrame

    def apply_date_range(self):
        """Apply the selected date range and process violations."""
        # First check: Database path validation
        if not os.path.exists(self.mandates_db_path):
            QMessageBox.critical(
                self,
                "Database Not Found",
                "Please configure the database path before proceeding.",
            )
            self.open_settings_dialog()
            if (
                hasattr(self, "carrier_list_pane")
                and self.carrier_list_pane is not None
            ):
                if hasattr(self.carrier_list_pane, "data_updated"):
                    self.carrier_list_pane.data_updated.connect(
                        lambda: self.retry_apply_date_range()
                    )
            return

        # Second check: Carrier List validation
        if not os.path.exists("carrier_list.json"):
            CustomInfoDialog.information(
                self,
                "Carrier List Required",
                "The carrier list needs to be configured and saved before processing dates.\n\n"
                "1. Configure your carrier list\n"
                "2. Click 'Save/Apply' to save your changes",
            )

            # Automatically open carrier list pane
            self.carrier_list_button.setChecked(True)
            self.toggle_carrier_list_pane()

            if (
                hasattr(self, "carrier_list_pane")
                and self.carrier_list_pane is not None
            ):
                self.carrier_list_pane.data_updated.connect(
                    lambda: self.retry_apply_date_range()
                )
            return

        # Third check: Carrier List content validation
        try:
            with open("carrier_list.json", "r") as json_file:
                carrier_list = pd.DataFrame(json.load(json_file))
                if carrier_list.empty:
                    QMessageBox.warning(
                        self,
                        "Empty Carrier List",
                        "The carrier list is empty. Please add carriers before proceeding.",
                    )
                    self.carrier_list_button.setChecked(True)
                    self.toggle_carrier_list_pane()
                    return
        except (json.JSONDecodeError, pd.errors.EmptyDataError):
            QMessageBox.critical(
                self,
                "Invalid Carrier List",
                "The carrier list file is corrupted. Please reconfigure the carrier list.",
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred while reading the carrier list: {str(e)}",
            )
            return

        # Create and show custom progress dialog
        progress = self.create_progress_dialog(
            "Processing Date Range", "Processing data..."
        )
        progress.show()

        def update_progress(value, message):
            progress.setValue(value)
            progress.setLabelText(message)
            QApplication.processEvents()

        try:
            # Initial setup (10%)
            update_progress(0, "Initializing...")
            QApplication.processEvents()

            # Validate the date selection
            if (
                not hasattr(self, "date_selection_pane")
                or self.date_selection_pane is None
            ):
                raise AttributeError("Date selection pane is not initialized.")

            if (
                not hasattr(self.date_selection_pane, "selected_range")
                or self.date_selection_pane.selected_range is None
            ):
                raise ValueError("No date range selected.")

            # Get the selected date range
            start_date, end_date = self.date_selection_pane.selected_range
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Fetch clock ring data (20%)
            update_progress(10, "Fetching clock ring data...")
            self.update_date_range_display(start_date_str, end_date_str)
            clock_ring_data = self.fetch_clock_ring_data(start_date_str, end_date_str)

            # Process carrier list (30%)
            update_progress(20, "Processing carrier list...")
            try:
                with open("carrier_list.json", "r") as json_file:
                    carrier_list = pd.DataFrame(json.load(json_file))

                # Ensure required columns exist in carrier_list
                required_columns = [
                    "carrier_name",
                    "list_status",
                    "route_s",
                    "hour_limit",
                    "effective_date",
                ]
                if not all(col in carrier_list.columns for col in required_columns):
                    raise ValueError(
                        f"Carrier list missing required columns: {required_columns}"
                    )

                # Normalize carrier_name for robust comparison
                carrier_list["carrier_name"] = (
                    carrier_list["carrier_name"].str.strip().str.lower()
                )
                clock_ring_data["carrier_name"] = (
                    clock_ring_data["carrier_name"].str.strip().str.lower()
                )

                # Drop existing list_status columns before merge if they exist
                columns_to_drop = ["list_status", "list_status_x", "list_status_y"]
                for col in columns_to_drop:
                    if col in clock_ring_data.columns:
                        clock_ring_data = clock_ring_data.drop(columns=[col])

                # Filter and merge clock ring data with all carrier list columns
                clock_ring_data = clock_ring_data[
                    clock_ring_data["carrier_name"].isin(carrier_list["carrier_name"])
                ]
                clock_ring_data = clock_ring_data.merge(
                    carrier_list, on="carrier_name", how="left"  # Merge all columns
                )

            except FileNotFoundError:
                QMessageBox.warning(
                    self,
                    "Missing Carrier List",
                    "Please configure and save the Carrier List before proceeding.",
                )
                return
            except Exception as e:
                print(f"Error processing carrier list: {str(e)}")
                clock_ring_data["list_status"] = "unknown"
                clock_ring_data["hour_limit"] = ""
                clock_ring_data["route_s"] = ""
                clock_ring_data["effective_date"] = ""
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Failed to process carrier list: {str(e)}\nProceeding with default values.",
                )

            # Clear existing data (35%)
            update_progress(30, "Clearing existing data...")
            self.vio_85d_tab.refresh_data(pd.DataFrame())
            self.vio_85f_tab.refresh_data(pd.DataFrame())
            self.vio_85f_ns_tab.refresh_data(pd.DataFrame())
            self.vio_85f_5th_tab.refresh_data(pd.DataFrame())
            self.vio_85g_tab.refresh_data(pd.DataFrame())
            self.vio_MAX12_tab.refresh_data(pd.DataFrame())
            self.vio_MAX60_tab.refresh_data(pd.DataFrame())
            self.remedies_tab.refresh_data(pd.DataFrame())

            # Process violations (40-90%)
            update_progress(40, "Processing violations...")
            self.update_violations_and_remedies(clock_ring_data, update_progress)

            # Update OTDL data (95%)
            update_progress(95, "Updating OTDL data...")
            if self.otdl_maximization_pane is None:
                self.otdl_maximization_pane = OTDLMaximizationPane(self)
            self.otdl_maximization_pane.refresh_data(clock_ring_data, clock_ring_data)

            # Complete (100%)
            update_progress(100, "Complete")
            self.statusBar().showMessage("Date range processing complete", 5000)

        except Exception as e:
            progress.cancel()
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred: {str(e)}"
            )
        finally:
            self.cleanup_progress_dialog(progress)

    def retry_apply_date_range(self):
        """Retry apply_date_range after carrier list is saved."""
        # Disconnect the one-time signal
        if hasattr(self, "carrier_list_pane") and self.carrier_list_pane is not None:
            try:
                self.carrier_list_pane.data_updated.disconnect()
            except TypeError:  # In case it's already disconnected
                pass

        # Check if carrier_list.json exists and is valid before proceeding
        if os.path.exists("carrier_list.json"):
            try:
                with open(
                    "carrier_list.json", "r", encoding="utf-8"
                ) as json_file:  # Added encoding
                    carrier_list = pd.DataFrame(json.load(json_file))
                    if not carrier_list.empty:
                        # Small delay to ensure UI updates are complete
                        QTimer.singleShot(100, self.apply_date_range)
            except Exception:
                pass  # If there's an error, just don't retry

    def clear_tabs_and_data(self):
        """Clear all existing tabs and reset associated data."""
        print("Clearing all tabs and resetting data for the new date range.")

        # Remove all tabs from the central tab widget
        while self.central_tab_widget.count() > 0:
            self.central_tab_widget.removeTab(0)

        # Reset all tab references to None
        self.vio_85d_tab = None
        self.vio_85f_tab = None
        self.vio_85f_ns_tab = None
        self.vio_85f_5th_tab = None
        self.vio_85g_tab = None
        self.vio_MAX12_tab = None
        self.vio_MAX60_tab = None
        self.remedies_tab = None

        # Reset other associated data
        self.current_data = pd.DataFrame()
        self.violations = None

    def init_menu_toolbar(self):
        """Initialize the menu bar and toolbar."""
        menu_bar = QMenuBar()

        # Style the menu bar with Material Dark Blue-Grey 700 (slightly lighter than title bar)
        menu_bar.setStyleSheet(
            """
            QMenuBar {
                background-color: #455A64;
                color: white;
                border: none;
                padding: 2px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
            }
            QMenuBar::item:selected {
                background-color: #546E7A;
            }
            QMenuBar::item:pressed {
                background-color: #37474F;
            }
            QMenu {
                background-color: #455A64;
                color: white;
                border: 1px solid #546E7A;
            }
            QMenu::item:selected {
                background-color: #546E7A;
            }
        """
        )

        # File menu
        self.file_menu = menu_bar.addMenu("File")

        # Clean Moves menu entry
        clean_moves_action = QAction("Clean Invalid Moves...", self)
        clean_moves_action.setShortcut("Ctrl+M")
        clean_moves_action.setStatusTip(
            "Clean moves entries with invalid route numbers"
        )
        clean_moves_action.triggered.connect(self.show_clean_moves_dialog)

        # Exit menu entry
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addActions(
            [clean_moves_action, exit_action]
        )  # Add both actions to the menu

        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        db_settings_action = QAction("Database Path", self)
        db_settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(db_settings_action)

        # Add Help menu
        help_menu = menu_bar.addMenu("Help")

        # Add Documentation action
        doc_action = QAction("Article 8 Violation Formulas Documentation", self)
        doc_action.triggered.connect(self.show_violation_documentation)
        help_menu.addAction(doc_action)

        # Optional: Add About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        self.setMenuBar(menu_bar)

    def open_settings_dialog(self):
        """Open the settings dialog to configure database path."""
        if self.settings_dialog is None or not self.settings_dialog.isVisible():
            self.settings_dialog = SettingsDialog(self.mandates_db_path, self)
            self.settings_dialog.show()
        else:
            self.settings_dialog.activateWindow()  # Bring existing window to front

    def init_carrier_list_pane(self):
        """Initialize the carrier list pane."""
        self.carrier_list_pane = CarrierListPane(self.mandates_db_path, parent=self)
        self.carrier_list_pane.request_apply_date_range.connect(self.apply_date_range)
        self.carrier_list_pane.hide()

    def handle_maximized_status_change(self, date_str, changes):
        """Handle changes to OTDL maximization status"""
        if "8.5.D" not in self.violations and "8.5.G" not in self.violations:
            return

        # If it's not a batch update (old signal format), convert to batch format
        if not isinstance(changes, dict):
            changes = {
                date_str: {
                    "is_maximized": changes,
                    "excused_carriers": self.otdl_maximization_pane.get_excused_carriers(
                        date_str
                    ),
                }
            }

        # Create and show progress dialog immediately
        progress = CustomProgressDialog(
            "Starting update...",
            None,  # No cancel button
            0,  # Minimum value
            100,  # Maximum value
            self,  # Parent widget
            "Updating Remedies",
        )
        progress.setWindowModality(Qt.ApplicationModal)
        progress.show()
        QApplication.processEvents()

        try:
            # Phase 1: Initial Setup (0-10%)
            progress.setLabelText("Initializing date range...")
            progress.setValue(5)
            QApplication.processEvents()

            # Get the selected date range from the date selection pane
            if (
                not hasattr(self, "date_selection_pane")
                or self.date_selection_pane is None
                or not hasattr(self.date_selection_pane, "selected_range")
            ):
                raise ValueError("No date range selected")

            start_date, end_date = self.date_selection_pane.selected_range
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Phase 2: Loading Data (10-30%)
            progress.setLabelText("Loading clock ring data...")
            progress.setValue(10)
            QApplication.processEvents()

            clock_ring_data = self.fetch_clock_ring_data(start_date_str, end_date_str)
            if clock_ring_data.empty:
                return

            # Phase 3: Processing Data (30-60%)
            progress.setLabelText("Loading carrier list...")
            progress.setValue(20)
            QApplication.processEvents()

            with open("carrier_list.json", "r") as json_file:
                carrier_list = pd.DataFrame(json.load(json_file))

            # Phase 4: Processing Data (30-60%)
            progress.setLabelText("Processing carrier data...")
            progress.setValue(30)
            QApplication.processEvents()

            carrier_list["carrier_name"] = (
                carrier_list["carrier_name"].str.strip().str.lower()
            )
            clock_ring_data["carrier_name"] = (
                clock_ring_data["carrier_name"].str.strip().str.lower()
            )

            # Phase 5: Merging Data (60-80%)
            progress.setLabelText("Merging carrier data...")
            progress.setValue(40)
            QApplication.processEvents()

            if "list_status" in clock_ring_data.columns:
                clock_ring_data = clock_ring_data.drop(columns=["list_status"])
            if "hour_limit" in clock_ring_data.columns:
                clock_ring_data = clock_ring_data.drop(columns=["hour_limit"])

            clock_ring_data = clock_ring_data.merge(
                carrier_list[["carrier_name", "list_status", "hour_limit"]],
                on="carrier_name",
                how="left",
            )

            # Phase 6: Updating Status (60-80%)
            progress.setLabelText("Processing maximization status...")
            progress.setValue(60)
            QApplication.processEvents()

            date_maximized_status = {}
            for d in pd.date_range(start_date_str, end_date_str):
                d_str = d.strftime("%Y-%m-%d")
                if d_str in changes:
                    date_maximized_status[d_str] = changes[d_str]
                else:
                    if hasattr(self.otdl_maximization_pane, "date_maximized"):
                        existing_status = (
                            self.otdl_maximization_pane.date_maximized.get(d_str, {})
                        )
                        if isinstance(existing_status, dict):
                            date_maximized_status[d_str] = existing_status
                        else:
                            date_maximized_status[d_str] = {"is_maximized": False}

            # Phase 7: Updating Violations (80-95%)
            if "8.5.D" in self.violations:
                progress.setLabelText("Updating 8.5.D violations...")
                progress.setValue(80)
                QApplication.processEvents()

                new_violations = detect_violations(
                    clock_ring_data,
                    "8.5.D Overtime Off Route",
                    date_maximized_status,
                )
                self.violations["8.5.D"] = new_violations
                self.vio_85d_tab.refresh_data(new_violations)

            if "8.5.G" in self.violations:
                progress.setLabelText("Updating 8.5.G violations...")
                progress.setValue(85)
                QApplication.processEvents()

                new_violations = detect_violations(
                    clock_ring_data, "8.5.G", date_maximized_status
                )
                self.violations["8.5.G"] = new_violations
                self.vio_85g_tab.refresh_data(new_violations)

            # Phase 8: Updating Summary (95-100%)
            progress.setLabelText("Updating violation summary...")
            progress.setValue(95)
            QApplication.processEvents()

            # Calculate and update remedies
            remedies_data = get_violation_remedies(clock_ring_data, self.violations)
            self.remedies_tab.refresh_data(remedies_data)

            progress.setLabelText("Update complete")
            progress.setValue(100)
            QApplication.processEvents()

        except Exception as e:
            print(f"Error in handle_maximized_status_change: {str(e)}")
            import traceback

            traceback.print_exc()
        finally:
            progress.close()

    def init_otdl_maximization_pane(self):
        """Initialize the OTDL maximization pane."""
        print("Initializing OTDL maximization pane...")

        self.otdl_maximization_pane = OTDLMaximizationPane(
            parent=self, carrier_list_pane=self.carrier_list_pane
        )

        # Connect the signal with the new signature
        self.otdl_maximization_pane.date_maximized_updated.connect(
            self.handle_maximized_status_change
        )

        # Explicitly connect the carrier list signal
        print("Connecting carrier list signal to OTDL pane...")
        self.carrier_list_pane.carrier_list_updated.connect(
            self.otdl_maximization_pane.handle_carrier_list_update
        )

        print("OTDL pane initialization complete")
        self.otdl_maximization_pane.hide()

    def on_carrier_list_updated(self, updated_carrier_data):
        """Update OTDL Maximization Pane when the carrier list changes."""
        # Filter for OTDL carriers in the updated carrier data
        otdl_carriers = updated_carrier_data[
            updated_carrier_data["list_status"] == "otdl"
        ]

        # Fetch clock ring data for the current date range
        clock_ring_data = self.fetch_clock_ring_data()

        # Filter clock ring data for OTDL carriers only
        clock_ring_data[
            clock_ring_data["carrier_name"].isin(otdl_carriers["carrier_name"])
        ].copy()

    def update_violations_and_remedies(
        self, clock_ring_data=None, progress_callback=None
    ):
        """Helper function to detect violations and update all tabs."""
        if clock_ring_data is None or clock_ring_data.empty:
            return

        # Define violation types and their display names
        violation_types = {
            "8.5.D": "8.5.D Overtime Off Route",
            "8.5.F": "8.5.F Overtime Over 10 Hours Off Route",
            "8.5.F NS": "8.5.F NS Overtime On a Non-Scheduled Day",
            "8.5.F 5th": "8.5.F 5th More Than 4 Days of Overtime in a Week",
            "8.5.G": "8.5.G",
            "MAX12": "MAX12 More Than 12 Hours Worked in a Day",
            "MAX60": "MAX60 More Than 60 Hours Worked in a Week",
        }

        # Initialize violations dictionary
        self.violations = {}

        # Get unique dates from clock ring data and initialize date_maximized_status
        unique_dates = (
            pd.to_datetime(clock_ring_data["rings_date"])
            .dt.strftime("%Y-%m-%d")
            .unique()
        )
        date_maximized_status = {date: {"is_maximized": False} for date in unique_dates}

        # Calculate progress increments
        total_steps = len(violation_types) * 2  # Detection and tab updates
        progress_per_step = 90 / total_steps  # Save 10% for remedies
        current_progress = 0

        try:
            # Detect violations (45% of progress)
            for key, violation_type in violation_types.items():
                if progress_callback:
                    progress_callback(
                        int(current_progress), f"Detecting {key} violations..."
                    )

                self.violations[key] = detect_violations(
                    clock_ring_data,
                    violation_type,
                    date_maximized_status if key in ["8.5.D", "8.5.G"] else None,
                )
                current_progress += progress_per_step
                if progress_callback:
                    progress_callback(
                        int(current_progress), f"Detected {key} violations"
                    )

            # Update violation tabs (45% of progress)
            tab_updates = [
                (self.vio_85d_tab, "8.5.D", "8.5.D violations"),
                (self.vio_85f_tab, "8.5.F", "8.5.F violations"),
                (self.vio_85f_ns_tab, "8.5.F NS", "8.5.F NS violations"),
                (self.vio_85f_5th_tab, "8.5.F 5th", "8.5.F 5th violations"),
                (self.vio_85g_tab, "8.5.G", "8.5.G violations"),
                (self.vio_MAX12_tab, "MAX12", "MAX12 violations"),
                (self.vio_MAX60_tab, "MAX60", "MAX60 violations"),
            ]

            for tab, key, description in tab_updates:
                if progress_callback:
                    progress_callback(
                        int(current_progress), f"Updating {description} tab..."
                    )
                tab.refresh_data(self.violations[key])
                current_progress += progress_per_step
                if progress_callback:
                    progress_callback(
                        int(current_progress), f"Updated {description} tab"
                    )

            # Calculate and update remedies (final 10%)
            if progress_callback:
                progress_callback(90, "Calculating final remedies...")

            remedies_data = get_violation_remedies(clock_ring_data, self.violations)
            self.remedies_tab.refresh_data(remedies_data)

            if progress_callback:
                progress_callback(100, "Complete")

        except Exception as e:
            print(f"Error in update_violations_and_remedies: {str(e)}")
            raise

    def on_carrier_data_updated(self, _):
        """Handle updates to the carrier list and refresh all tabs.

        Actually uses the JSON file for applying updates to the fetched clock ring data.
        Just updating the data without clicking 'Save Carrier List' will not update the views.
        """
        print("MainApp: Received data_updated signal.")

        # Load the most up-to-date carrier data from the JSON file
        try:
            with open("carrier_list.json", "r") as json_file:
                carrier_list = pd.DataFrame(json.load(json_file))
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "carrier_list.json not found.")
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load carrier_list.json: {str(e)}"
            )
            return

        # Fetch clock ring data from the database
        clock_ring_data = self.fetch_clock_ring_data()
        if not clock_ring_data.empty:
            # Merge clock ring data with the carrier list from JSON
            clock_ring_data = clock_ring_data.merge(
                carrier_list[["carrier_name", "list_status"]],
                on="carrier_name",
                how="left",
                suffixes=("_db", "_updated"),
            )

            # Consolidate list_status
            clock_ring_data["list_status"] = clock_ring_data[
                "list_status_updated"
            ].combine_first(clock_ring_data["list_status_db"])
            clock_ring_data.drop(
                columns=["list_status_db", "list_status_updated"], inplace=True
            )

        # Refresh other components
        if self.otdl_maximization_pane:
            print("Refreshing OTDLMaximizationPane with updated data.")
            self.otdl_maximization_pane.refresh_data(clock_ring_data, carrier_list)

        # Update violations and remedies
        self.update_violations_and_remedies(clock_ring_data)

    # This query generates the base dataframe for the entire program.
    # The resulting dataframe will be modified by subsequent methods.
    def fetch_clock_ring_data(self, start_date=None, end_date=None):
        """Fetch clock ring data for the selected date range from the working database.

        Important note on date handling:
        The SQL query uses `rings_date >= DATE(?)` for the start date and
        `rings_date < DATE(?, '+1 day')` for the end date to ensure we get
        all records for the entire end date. This is because SQLite's DATE()
        function truncates times to midnight, so using <= would miss records
        later in the day. By using < next_day, we include all records up to
        but not including midnight of the next day.

        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: DataFrame containing clock ring data with columns:
                - carrier_name
                - rings_date
                - list_status
                - total
                - moves
                - code
                - leave_type
                - leave_time
                - display_indicator
        """
        # First validate database path
        if not self.eightbox_db_path or not os.path.exists(self.eightbox_db_path):
            QMessageBox.critical(
                self,
                "Database Error",
                "No valid database path configured.\n"
                "Please set a valid database path in Settings.",
            )
            return pd.DataFrame(
                columns=[
                    "carrier_name",
                    "rings_date",
                    "list_status",
                    "total",
                    "moves",
                    "code",
                    "leave_type",
                    "leave_time",
                    "display_indicator",
                ]
            )

        try:
            # If no dates provided, try to get them from the date selection pane
            if start_date is None or end_date is None:
                if (
                    not hasattr(self, "date_selection_pane")
                    or self.date_selection_pane is None
                    or not hasattr(self.date_selection_pane, "selected_range")
                    or self.date_selection_pane.selected_range is None
                ):
                    raise ValueError("No valid date range selected.")

                start_date, end_date = self.date_selection_pane.selected_range
                start_date = start_date.strftime("%Y-%m-%d")
                end_date = end_date.strftime("%Y-%m-%d")

            # Convert string dates to datetime.date objects
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date).date()
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date).date()

            params = ClockRingQueryParams(
                start_date=start_date,
                end_date=end_date,
                db_path=self.eightbox_db_path,  # Use eightbox_db_path here
            )

            data, error = self.db_service.fetch_clock_ring_data(params)
            if error:
                # Error handler already called by service
                return pd.DataFrame(
                    columns=[
                        "carrier_name",
                        "rings_date",
                        "list_status",
                        "total",
                        "moves",
                        "code",
                        "leave_type",
                        "leave_time",
                        "display_indicator",
                    ]
                )

            return data

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred: {str(e)}"
            )
            return pd.DataFrame(
                columns=[
                    "carrier_name",
                    "rings_date",
                    "list_status",
                    "total",
                    "moves",
                    "code",
                    "leave_type",
                    "leave_time",
                    "display_indicator",
                ]
            )

    def show_violation_documentation(self):
        """Show the documentation dialog."""
        from documentation_dialog import DocumentationDialog

        doc_dialog = DocumentationDialog(self)
        doc_dialog.exec_()

    def show_about_dialog(self):
        """Show the About dialog using our custom themed dialog."""

        about_text = f"""
        <h3>Eightbox - Article 8 Violation Detection</h3>
        <p>A tool for detecting and displaying Article 8 violations.</p>
        <p>Created by: Branch 815</p>
        <p>Version {self.VERSION}</p>
        <p>Build: {self.BUILD_TIME}</p>
        """

        CustomInfoDialog.information(self, "About Eightbox", about_text)

    def load_carrier_data(self):
        """Load carrier data from the database."""
        try:
            self.carrier_list_pane.load_carrier_data()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load carrier data: {str(e)}"
            )

    def export_violations(self):
        """Export violations to Excel."""
        try:
            self.remedies_tab.export_to_excel()
            QMessageBox.information(self, "Success", "Violations exported successfully")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to export violations: {str(e)}"
            )

    def show_settings(self):
        """Show the settings dialog.

        Opens the settings dialog for configuring application options
        including database path and other preferences.
        """
        if self.settings_dialog is None or not self.settings_dialog.isVisible():
            from settings_dialog import SettingsDialog

            self.settings_dialog = SettingsDialog(self.mandates_db_path, self)
            self.settings_dialog.show()
        else:
            self.settings_dialog.activateWindow()  # Bring existing window to front

    def show_documentation(self):
        """Show the documentation dialog.

        Opens the documentation window containing usage instructions,
        keyboard shortcuts, and other help information.
        """
        from documentation_dialog import DocumentationDialog

        doc_dialog = DocumentationDialog(self)
        doc_dialog.exec_()

    def minimize_to_tray(self):
        """Minimize the application window.

        Handles proper window minimization while maintaining
        the custom window frame.
        """
        self.showMinimized()

    def maximize_restore(self):
        """Toggle between maximized and normal window states.

        Handles proper window maximization/restoration while
        maintaining the custom window frame.
        """
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def get_violation_tab_by_type(self, violation_type):
        """Get the violation tab instance for a given violation type.

        Args:
            violation_type: The type of violation to get the tab for

        Returns:
            The violation tab instance or None if not found
        """
        if violation_type == "8.5.D":
            return self.vio_85d_tab
        if violation_type == "8.5.F":
            return self.vio_85f_tab
        if violation_type == "8.5.F NS":
            return self.vio_85f_ns_tab
        if violation_type == "8.5.F 5th":
            return self.vio_85f_5th_tab
        if violation_type == "8.5.G":
            return self.vio_85g_tab
        if violation_type == "MAX12":
            return self.vio_MAX12_tab
        if violation_type == "MAX60":
            return self.vio_MAX60_tab
        if violation_type == "Summary":
            return self.remedies_tab
        return None

    def apply_global_carrier_filter(self, text):
        """Apply carrier filter text across all violation tabs.

        Args:
            text (str): The filter text to apply
        """
        # Get the current active tab
        current_tab = self.central_tab_widget.currentWidget()

        # Apply filter to each violation tab
        for tab in [
            self.vio_85d_tab,
            self.vio_85f_tab,
            self.vio_85f_ns_tab,
            self.vio_85f_5th_tab,
            self.vio_85g_tab,
            self.vio_MAX12_tab,
            self.vio_MAX60_tab,
            self.remedies_tab,
        ]:
            if hasattr(tab, "filter_carriers"):
                tab.filter_carriers(text, "name")
                # Only update stats for the currently visible tab
                if tab == current_tab:
                    tab.update_stats()

    def on_carrier_filter_changed(self, text):
        """Handle changes to the carrier filter text.

        Args:
            text (str): The filter text entered by the user
        """
        # Apply filter to each violation tab
        for tab in [
            self.vio_85d_tab,
            self.vio_85f_tab,
            self.vio_85f_ns_tab,
            self.vio_85f_5th_tab,
            self.vio_85g_tab,
            self.vio_MAX12_tab,
            self.vio_MAX60_tab,
            self.remedies_tab,
        ]:
            if hasattr(tab, "filter_carriers"):
                tab.filter_carriers(text, "name")

    def apply_carrier_filter(self, text):
        """Apply carrier name filter to the current tab.

        Args:
            text (str): The filter text to apply
        """
        current_tab = self.central_tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, "apply_carrier_filter"):
            current_tab.apply_carrier_filter(text.lower())
            # Update stats after filtering
            if hasattr(current_tab, "update_stats"):
                current_tab.update_stats()

    def update_date_range_display(self, start_date, end_date):
        """Update the date range display in the filter row.

        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
        """
        if hasattr(self, "date_range_label"):
            if start_date and end_date:
                self.date_range_label.setText(
                    f"Selected Date Range: {start_date} to {end_date}"
                )
            else:
                self.date_range_label.setText("Selected Date Range: None")

    def toggle_date_selection_pane(self):
        """Toggle the Date Selection Pane and button state."""
        if not hasattr(self, "date_selection_pane") or self.date_selection_pane is None:
            # Initialize with the eightbox database path
            self.date_selection_pane = DateSelectionPane(self.eightbox_db_path, self)
            # Connect the date range selected signal
            self.date_selection_pane.date_range_selected.connect(
                self.on_date_range_selected
            )

        if self.date_selection_pane.isVisible():
            self.date_selection_pane.hide()
            self.date_selection_button.setChecked(False)
        else:
            self.date_selection_pane.show()
            # Set a reasonable initial size for the selector
            self.date_selection_pane.resize(600, 500)
            self.date_selection_button.setChecked(True)

    def on_date_range_selected(self, start_date, end_date):
        """Handle when a date range is selected.

        Args:
            start_date (datetime): Start date of selected range
            end_date (datetime): End date of selected range
        """
        # Update the date range display
        self.update_date_range_display(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )

        # Process the selected date range
        self.apply_date_range()

    def toggle_carrier_list_pane(self):
        """Toggle the Carrier List Pane and button state."""
        if not hasattr(self, "carrier_list_pane") or self.carrier_list_pane is None:
            self.carrier_list_pane = CarrierListPane(self.mandates_db_path, self)

        if self.carrier_list_pane.isVisible():
            self.carrier_list_pane.hide()
            self.carrier_list_button.setChecked(False)
        else:
            self.carrier_list_pane.show()
            self.carrier_list_pane.resize(650, 400)
            self.carrier_list_button.setChecked(True)

    def toggle_otdl_maximization_pane(self):
        """Toggle the OTDL Maximization Pane and button state."""
        if (
            not hasattr(self, "otdl_maximization_pane")
            or self.otdl_maximization_pane is None
        ):
            self.otdl_maximization_pane = OTDLMaximizationPane(
                self.carrier_list_pane, self
            )

        if self.otdl_maximization_pane.isVisible():
            self.otdl_maximization_pane.hide()
            self.otdl_maximization_button.setChecked(False)
        else:
            self.otdl_maximization_pane.show()
            self.otdl_maximization_pane.setMinimumSize(1053, 300)
            self.otdl_maximization_button.setChecked(True)

    def create_progress_dialog(self, title="Processing...", initial_text=""):
        """Create and track a new progress dialog.

        Args:
            title (str): Title for the progress dialog
            initial_text (str): Initial message to display

        Returns:
            CustomProgressDialog: The created progress dialog
        """
        progress = CustomProgressDialog(initial_text, "", 0, 100, self, title=title)
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        self.active_progress_dialogs.append(progress)
        return progress

    def cleanup_progress_dialog(self, progress):
        """Clean up and close a progress dialog.

        Args:
            progress (CustomProgressDialog): The progress dialog to clean up
        """
        if progress in self.active_progress_dialogs:
            self.active_progress_dialogs.remove(progress)
        progress.close()

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        # Update size grip position and ensure it stays visible
        self.size_grip.move(
            self.width() - 20, self.height() - 20
        )  # Adjusted for new size
        self.size_grip.raise_()

    def init_connections(self):
        """Initialize signal/slot connections."""
        # Replace lambda with direct method reference
        QTimer.singleShot(100, self.apply_date_range)

    def initialize_eightbox_database(self, source_db_path=None):
        """Initialize the eightbox.sqlite database.

        Args:
            source_db_path (str, optional): Path to source database. Defaults to None.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        target_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "eightbox.sqlite"
        )
        initializer = DatabaseInitializer(target_path, source_db_path, self)
        return initializer.initialize()

    def show_clean_moves_dialog(self):
        """Show the Clean Moves dialog.

        Detects moves entries with invalid route numbers and allows
        the user to clean them. Only shows entries for WAL and NL carriers
        from the carrier list.
        """
        # Get current data from the date range
        current_data = self.fetch_clock_ring_data()

        if current_data.empty:
            CustomWarningDialog.warning(
                self, "No Data", "Please select a date range first."
            )
            return

        # Get valid routes
        valid_routes = get_valid_routes(self.eightbox_db_path)
        if not valid_routes:
            CustomWarningDialog.warning(
                self, "Error", "Failed to get valid route numbers from database."
            )
            return

        # Load carrier list
        try:
            with open("carrier_list.json", "r") as f:
                carrier_list = json.load(f)
                # Only include WAL and NL carriers
                valid_carriers = {
                    carrier["carrier_name"].lower()
                    for carrier in carrier_list
                    if carrier["list_status"].lower() in ["wal", "nl"]
                }
        except Exception as e:
            CustomWarningDialog.warning(
                self, "Error", f"Failed to load carrier list: {str(e)}"
            )
            return

        # Detect invalid moves
        invalid_moves = detect_invalid_moves(current_data, self.eightbox_db_path)
        if invalid_moves.empty:
            CustomInfoDialog.information(
                self,
                "No Invalid Moves",
                "No moves entries with invalid route numbers were found.",
            )
            return

        # Filter invalid moves to only include WAL and NL carriers from the carrier list
        invalid_moves = invalid_moves[
            invalid_moves["carrier_name"].str.lower().isin(valid_carriers)
        ]

        if invalid_moves.empty:
            CustomInfoDialog.information(
                self,
                "No Invalid Moves",
                "No moves entries with invalid route numbers were found for WAL and NL carriers.",
            )
            return

        # Create and show dialog
        dialog = CleanMovesDialog(invalid_moves, valid_routes, self)
        dialog.moves_cleaned.connect(
            lambda cleaned: self.handle_cleaned_moves(cleaned, current_data)
        )
        dialog.exec_()

    def handle_cleaned_moves(self, cleaned_moves, current_data):
        """Handle cleaned moves data from the dialog.

        Args:
            cleaned_moves: Dictionary mapping (carrier, date) to cleaned moves string
            current_data: The current DataFrame of clock ring data
        """
        if not cleaned_moves:
            return

        # Create progress dialog
        progress = self.create_progress_dialog(
            "Updating Moves", "Applying cleaned moves data..."
        )
        progress.show()

        try:
            # Phase 1: Update moves (0-30%)
            progress.setLabelText("Updating moves data...")
            progress.setValue(10)
            QApplication.processEvents()

            for (carrier, date), moves in cleaned_moves.items():
                mask = (current_data["carrier_name"] == carrier) & (
                    current_data["rings_date"] == date
                )
                current_data.loc[mask, "moves"] = moves

            progress.setValue(30)
            QApplication.processEvents()

            # Phase 1.5: Merge carrier list data (30-50%)
            progress.setLabelText("Updating carrier data...")
            progress.setValue(40)
            QApplication.processEvents()

            try:
                with open("carrier_list.json", "r") as json_file:
                    carrier_list = pd.DataFrame(json.load(json_file))

                # Normalize carrier names
                carrier_list["carrier_name"] = (
                    carrier_list["carrier_name"].str.strip().str.lower()
                )
                current_data["carrier_name"] = (
                    current_data["carrier_name"].str.strip().str.lower()
                )

                # Drop existing list_status and hour_limit columns if they exist
                columns_to_drop = [
                    "list_status",
                    "list_status_x",
                    "list_status_y",
                    "hour_limit",
                ]
                for col in columns_to_drop:
                    if col in current_data.columns:
                        current_data = current_data.drop(columns=[col])

                # Merge with carrier list data
                current_data = current_data.merge(
                    carrier_list[["carrier_name", "list_status", "hour_limit"]],
                    on="carrier_name",
                    how="left",
                )

            except Exception as e:
                print(f"Error merging carrier list data: {e}")
                current_data["list_status"] = "unknown"
                current_data["hour_limit"] = 12.00

            progress.setValue(50)
            QApplication.processEvents()

            # Phase 2: Reprocess violations (50-90%)
            progress.setLabelText("Reprocessing violations...")
            progress.setValue(60)
            QApplication.processEvents()

            self.update_violations_and_remedies(current_data)

            progress.setValue(90)
            QApplication.processEvents()

            # Phase 3: Cleanup (90-100%)
            progress.setLabelText("Finalizing changes...")
            progress.setValue(100)
            QApplication.processEvents()

        except Exception as e:
            # Clean up progress dialog before showing error
            self.cleanup_progress_dialog(progress)
            CustomWarningDialog.warning(
                self, "Error", f"Failed to process cleaned moves: {str(e)}"
            )
            return
        # Clean up progress dialog before showing success
        self.cleanup_progress_dialog(progress)

        # Show success message after progress dialog is cleaned up
        CustomInfoDialog.information(
            self, "Success", "Moves data has been cleaned and violations reprocessed."
        )

    def _handle_database_error(self, error):
        """Handle database errors with appropriate GUI feedback."""
        QMessageBox.critical(self, "Database Error", error.message)

    def _init_container(self):
        """Initialize the main container and layout."""
        # Create main container widget
        self.container = QWidget()
        self.container.setObjectName("mainContainer")

        # Create main container layout
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.container.setLayout(container_layout)

        # Create menu content widget
        self.menu_content_widget = QWidget()
        self.menu_content_widget.setObjectName("menuContent")
        self.menu_content_layout = QVBoxLayout()
        self.menu_content_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_content_layout.setSpacing(0)
        self.menu_content_widget.setLayout(self.menu_content_layout)

        # Add title bar and menu content to container
        container_layout.addWidget(self.title_bar)
        container_layout.addWidget(self.menu_content_widget)

        # Set as central widget
        self.setCentralWidget(self.container)

    def _init_title_bar(self):
        """Initialize the custom title bar."""
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setObjectName("titleBar")

    def _init_tabs(self):
        """Initialize all tabs and panes."""
        # Initialize dynamic panes
        self.date_selection_pane = None
        self.carrier_list_pane = None
        self.otdl_maximization_pane = None

        # Configure main tab bar
        self.central_tab_widget.setDocumentMode(True)
        self.central_tab_widget.setMovable(False)
        self.central_tab_widget.setTabsClosable(False)

        # Set tab widget style
        self.central_tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
                background-color: #121212;
            }
            QTabBar {
                qproperty-drawBase: 0;
            }
            QTabBar::tab {
                background-color: #1E1E1E;
                color: rgba(255, 255, 255, 0.6);
                padding: 8px 16px;
                border: none;
                border-right: 1px solid #2D2D2D;
                min-width: 80px;
                font: 11px;
            }
            QTabBar::tab:selected {
                color: #BB86FC;
                background-color: rgba(187, 134, 252, 0.12);
                border-bottom: 2px solid #BB86FC;
            }
            QTabBar::tab:hover {
                background-color: rgba(187, 134, 252, 0.08);
                color: #CBB0FF;
            }
            QTabBar::scroller {
                width: 0px;
            }
        """
        )

        # Initialize violation tabs
        self.init_85d_tab()
        self.init_85f_tab()
        self.init_85f_ns_tab()
        self.init_85f_5th_tab()
        self.init_85g_tab()
        self.init_MAX12_tab()
        self.init_MAX60_tab()
        self.init_remedies_tab()

        # Connect tab change signal
        self.central_tab_widget.currentChanged.connect(self.handle_main_tab_change)

        # Initialize carrier list and OTDL panes
        self.init_carrier_list_pane()
        self.init_otdl_maximization_pane()

        # Initialize settings dialog reference
        self.settings_dialog = None

        # Add export action to file menu
        export_all_action = QAction("Generate All Excel Spreadsheets", self)
        export_all_action.triggered.connect(self.excel_exporter.export_all_violations)
        self.file_menu.addAction(export_all_action)

    def _init_sub_tab_bar(self, tab_widget):
        """Initialize a sub-tab bar with compact styling."""
        sub_tab_bar = QTabBar()
        sub_tab_bar.setExpanding(False)
        sub_tab_bar.setFixedHeight(28)  # Smaller height for sub-tabs
        tab_widget.setTabBar(sub_tab_bar)

        # Set sub-tab specific style
        tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
                background-color: #121212;
                padding-top: 2px;
            }
            QTabBar {
                qproperty-drawBase: 0;
            }
            QTabBar::tab {
                background-color: #1A1A1A;
                color: rgba(255, 255, 255, 0.6);
                padding: 6px 12px;
                min-width: 60px;
                margin: 0;
                border-right: 1px solid #2D2D2D;
                font-size: 10px;
                font-weight: normal;
                text-transform: uppercase;
                letter-spacing: 0.05px;
            }
            QTabBar::tab:hover {
                background-color: rgba(187, 134, 252, 0.08);
                color: #CBB0FF;
            }
            QTabBar::tab:selected {
                color: #BB86FC;
                border-bottom: 2px solid #BB86FC;
                background-color: rgba(187, 134, 252, 0.12);
                border-right: 1px solid #BB86FC;
                font-weight: 500;
            }
            QTabBar::scroller {
                width: 0px;
            }
        """
        )

    def _init_size_grip(self):
        """Initialize the custom size grip."""
        self.size_grip = CustomSizeGrip(self)
        self.size_grip.setObjectName("sizeGrip")
        self.size_grip.setStyleSheet("background: transparent;")
        self.size_grip.move(self.width() - 20, self.height() - 20)
        self.size_grip.raise_()


if __name__ == "__main__":
    # Run the application
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()

    # Run the event loop
    exit_code = app.exec_()

    # Exit the program
    sys.exit(exit_code)
