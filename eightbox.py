"""Main graphical user interface for the application.

Implements the primary window and core UI functionality, coordinating between
different panes and managing the overall application state and user interactions.
"""

import os
import sys

import pandas as pd  # Data manipulation
from PyQt5.QtCore import (
    QRect,
    Qt,
    QTimer,
    qInstallMessageHandler,
)
from PyQt5.QtGui import QColor  # Add QColor import
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

from carrier_list import CarrierListPane
from clean_moves.clean_moves_manager import MovesManager
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
from date_range_manager import DateRangeManager
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
from theme import RGB_IRIS  # Import RGB_IRIS color constant
from theme import (
    CLOSE_BUTTON_STYLE,
    FILTER_BUTTON_ROW_STYLE,
    FILTER_ROW_STYLE,
    MENU_BAR_STYLE,
    SIZE_GRIP_STYLE,
    SUB_TAB_STYLE,
    TAB_WIDGET_STYLE,
    TITLE_BAR_STYLE,
    TOP_BUTTON_ROW_STYLE,
    apply_material_dark_theme,
)

VERSION = "2024.1.5.1"  # Updated by release.py
BUILD_TIME = "2024-12-29 15:07"  # Updated by release.py


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
        self.setStyleSheet(TITLE_BAR_STYLE)

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
        close_btn.setStyleSheet(CLOSE_BUTTON_STYLE)
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
        date_range_manager (DateRangeManager): Manages date range operations
        moves_manager (MovesManager): Manages moves cleaning operations
    """

    VERSION = "2024.1.5.1"  # Updated by release.py
    BUILD_TIME = "2024-12-29 15:07"  # Updated by release.py

    def __init__(self):
        super().__init__()
        # Add flag for tracking updates
        self.otdl_update_in_progress = False

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

        # Initialize date range manager
        self.date_range_manager = DateRangeManager(self)

        # Initialize moves manager
        self.moves_manager = MovesManager(self)

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
        button_container.setStyleSheet(TOP_BUTTON_ROW_STYLE)

        # Create buttons with icons
        self.date_selection_button = QPushButton("Date Selection")
        self.date_selection_button.setObjectName("primary")
        self.date_selection_button.setCheckable(True)
        self.date_selection_button.clicked.connect(self.toggle_date_selection_pane)

        self.carrier_list_button = QPushButton("Carrier List")
        self.carrier_list_button.setObjectName("primary")
        self.carrier_list_button.setCheckable(True)
        self.carrier_list_button.clicked.connect(self.toggle_carrier_list_pane)

        self.otdl_maximization_button = QPushButton("OTDL Maximization")
        self.otdl_maximization_button.setObjectName("primary")
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
        filter_container.setStyleSheet(FILTER_ROW_STYLE)

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
        filter_row.setStyleSheet(FILTER_BUTTON_ROW_STYLE)

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
        btn.setObjectName("secondary")
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
        """Interface method called by violation tabs to notify parent of stat changes.

        This implementation intentionally does nothing as the main app doesn't need
        to track these stats, but the method exists to satisfy the interface
        expected by the violation tabs.

        Args:
            total (int): Total number of carriers
            wal (int): Number of WAL carriers
            nl (int): Number of NL carriers
            otdl (int): Number of OTDL carriers
            ptf (int): Number of PTF carriers
            violations (int): Number of carriers with violations
        """
        # Intentionally empty - main app doesn't need to track these stats

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
        self.date_range_manager.apply_date_range()

    def update_otdl_violations(
        self, clock_ring_data, progress_callback=None, date_maximized_status=None
    ):
        """Update only OTDL-related violations (8.5.D and 8.5.G) and their tabs."""
        self.date_range_manager.update_otdl_violations(
            clock_ring_data, progress_callback, date_maximized_status
        )

    def handle_maximized_status_change(self, date_str, changes):
        """Handle changes to OTDL maximization status"""
        self.date_range_manager.handle_maximized_status_change(date_str, changes)

    def update_violations_and_remedies(
        self, clock_ring_data=None, progress_callback=None
    ):
        """Helper function to detect violations and update all tabs."""
        self.date_range_manager.update_violations_and_remedies(
            clock_ring_data, progress_callback
        )

    def on_carrier_data_updated(self, updated_carrier_data):
        """Handle updates to the carrier list and refresh all tabs."""
        self.date_range_manager.on_carrier_data_updated(updated_carrier_data)

    # This query generates the base dataframe for the entire program.
    # The resulting dataframe will be modified by subsequent methods.
    def fetch_clock_ring_data(self, start_date=None, end_date=None):
        """Fetch clock ring data for the selected date range from the working database.

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

            # Create query parameters and let database service handle date conversion
            params = ClockRingQueryParams(
                start_date=start_date,
                end_date=end_date,
                db_path=self.eightbox_db_path,
                carrier_list_path="carrier_list.json",
            )

            # Use database service to fetch data
            data, error = self.db_service.fetch_clock_ring_data(params)

            if error:
                # Show error dialog
                CustomWarningDialog.warning(self, "Database Error", error.message)
                return self.db_service.get_empty_clock_ring_frame()

            return data

        except ValueError as e:
            if str(e) == "No valid date range selected.":
                CustomInfoDialog.information(
                    self, "No Date Range", "Please select a date range first."
                )
            else:
                CustomWarningDialog.warning(
                    self, "Error", f"An unexpected error occurred: {str(e)}"
                )
            return self.db_service.get_empty_clock_ring_frame()
        except Exception as e:
            CustomWarningDialog.warning(
                self, "Error", f"An unexpected error occurred: {str(e)}"
            )
            return self.db_service.get_empty_clock_ring_frame()

    def show_violation_documentation(self):
        """Show the documentation dialog."""
        from documentation_dialog import DocumentationDialog

        doc_dialog = DocumentationDialog(self)
        doc_dialog.exec_()

    def show_about_dialog(self):
        """Show the About dialog using our custom themed dialog."""
        about_text = f"""
        <div style='margin-bottom: 12px;'>
            <h3 style='color: {QColor(*RGB_IRIS).name()}; margin-bottom: 8px;'>
            Eightbox - Article 8 Violation Detection</h3>
            <p style='margin: 4px 0;'>A tool for detecting and displaying Article 8 violations.</p>
            <p style='margin: 4px 0;'>Created by: Branch 815</p>
            <p style='margin: 4px 0;'>Version {self.VERSION}</p>
            <p style='margin: 4px 0;'>Build: {self.BUILD_TIME}</p>
        </div>
        """

        dialog = CustomInfoDialog("About Eightbox", about_text, self)
        dialog.icon_label.setObjectName("iconLabel")
        dialog.message_label.setObjectName("messageLabel")
        dialog.exec_()

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
        progress = CustomProgressDialog(
            initial_text, "Cancel", 0, 100, self, title=title
        )
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
        self.central_tab_widget.setStyleSheet(TAB_WIDGET_STYLE)

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

        tab_widget.setTabBar(sub_tab_bar)

        # Set sub-tab specific style
        tab_widget.setStyleSheet(SUB_TAB_STYLE)

    def _init_size_grip(self):
        """Initialize the custom size grip."""
        self.size_grip = CustomSizeGrip(self)
        self.size_grip.setObjectName("sizeGrip")
        self.size_grip.setStyleSheet(SIZE_GRIP_STYLE)
        self.size_grip.move(self.width() - 20, self.height() - 20)
        self.size_grip.raise_()

    def retry_apply_date_range(self):
        """Retry apply_date_range after carrier list is saved."""
        self.date_range_manager.retry_apply_date_range()

    def clear_tabs_and_data(self):
        """Clear all existing tabs and reset associated data."""
        self.date_range_manager.clear_tabs_and_data()

    def init_menu_toolbar(self):
        """Initialize the menu bar and toolbar."""
        menu_bar = QMenuBar()

        # Style the menu bar with Material Dark Blue-Grey 700
        menu_bar.setStyleSheet(MENU_BAR_STYLE)

        # File menu
        self.file_menu = menu_bar.addMenu("File")

        # Clean Moves menu entry
        clean_moves_action = QAction("Clean Invalid Moves...", self)
        clean_moves_action.setShortcut("Ctrl+M")
        clean_moves_action.setStatusTip(
            "Clean moves entries with invalid route numbers"
        )
        clean_moves_action.triggered.connect(self.moves_manager.show_clean_moves_dialog)

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


if __name__ == "__main__":
    # Run the application
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()

    # Run the event loop
    exit_code = app.exec_()

    # Exit the program
    sys.exit(exit_code)
