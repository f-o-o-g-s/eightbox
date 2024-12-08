"""Main graphical user interface for the application.

Implements the primary window and core UI functionality, coordinating between
different panes and managing the overall application state and user interactions.
"""

import json
import os
import sqlite3
import sys

import pandas as pd  # Data manipulation
from PyQt5.QtCore import (
    Qt,
    QTimer,
    qInstallMessageHandler,
)
from PyQt5.QtWidgets import (  # Specific widget import for header configuration
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from carrier_list_pane import CarrierListPane
from custom_widgets import (
    CustomInfoDialog,
    CustomProgressDialog,
    CustomWarningDialog,
)

# Custom modules
from date_selection_pane import DateSelectionPane
from excel_export import ExcelExporter
from otdl_maximization_pane import OTDLMaximizationPane

# Theme colors
from theme import apply_material_dark_theme
from utils import set_display
from violation_85d_tab import Violation85dTab
from violation_85f_5th_tab import Violation85f5thTab
from violation_85f_ns_tab import Violation85fNsTab
from violation_85f_tab import Violation85fTab
from violation_detection import (
    detect_violations,
    get_violation_remedies,
)
from violation_max12_tab import ViolationMax12Tab
from violation_max60_tab import ViolationMax60Tab
from violations_summary_tab import ViolationRemediesTab


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
        self.maximize_restore()


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
        vio_MAX12_tab (ViolationMax12Tab): Tab for 12-hour limit violations
        vio_MAX60_tab (ViolationMax60Tab): Tab for 60-hour limit violations
        remedies_tab (ViolationRemediesTab): Summary tab for all violations
        carrier_list_pane (CarrierListPane): Carrier management interface
        otdl_maximization_pane (OTDLMaximizationPane): OTDL assignment interface
    """

    VERSION = "2024.0.2.0"  # Updated by release.py
    BUILD_TIME = "2024-12-08 12:56"  # Updated by release.py

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create the excel exporter first
        self.excel_exporter = ExcelExporter(self)

        # Track current filter state
        self.current_status_filter = "all"

        # Create main container
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container.setLayout(container_layout)

        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        container_layout.addWidget(self.title_bar)

        # Apply material dark theme
        apply_material_dark_theme(QApplication.instance())

        self.setWindowTitle("Eightbox - Branch 815 - Violation Detection")
        self.setGeometry(100, 100, 1200, 800)

        # Hide status bar
        self.statusBar().hide()

        # Initialize database path
        self.mandates_db_path = self.auto_detect_klusterbox_path()

        # Create a widget to hold the menu and main content
        menu_content_widget = QWidget()
        menu_content_layout = QVBoxLayout()
        menu_content_layout.setContentsMargins(0, 0, 0, 0)
        menu_content_layout.setSpacing(0)
        menu_content_widget.setLayout(menu_content_layout)

        # Setup main menu and toolbar
        self.init_menu_toolbar()
        menu_content_layout.addWidget(self.menuBar())

        # Initialize dynamic panes
        self.date_selection_pane = None
        self.init_carrier_list_pane()
        self.init_otdl_maximization_pane()

        # Main layout with buttons and central tab widget
        self.main_layout = QVBoxLayout()
        
        # Initialize top button row (utility buttons only)
        self.init_top_button_row()

        # Central tab widget for reports
        self.central_tab_widget = QTabWidget()
        self.main_layout.addWidget(self.central_tab_widget)

        # Initialize bottom filter row
        self.init_filter_button_row()

        # Connect the main tab change signal
        self.central_tab_widget.currentChanged.connect(self.handle_main_tab_change)

        # Add main layout to menu content layout
        menu_content_layout.addLayout(self.main_layout)

        # Add menu content widget to container layout
        container_layout.addWidget(menu_content_widget)

        self.setCentralWidget(container)

        # Initialize Violation Tabs
        self.init_85d_tab()
        self.init_85f_tab()
        self.init_85f_ns_tab()
        self.init_85f_5th_tab()
        self.init_MAX12_tab()
        self.init_MAX60_tab()
        self.init_remedies_tab()

        self.settings_dialog = None  # Initialize as None

        # Update the menu action to use the new exporter
        export_all_action = QAction("Generate All Excel Spreadsheets", self)
        export_all_action.triggered.connect(self.excel_exporter.export_all_violations)
        self.file_menu.addAction(export_all_action)

    def handle_main_tab_change(self, index):
        """Handle switching between main violation tabs.
        
        Maintains the current filter state across tab switches.
        
        Args:
            index (int): Index of the newly selected tab
        """
        # Get the current tab
        current_tab = self.central_tab_widget.widget(index)
        
        # If we have a valid tab and current filter state
        if current_tab:
            # Apply carrier filter if there is any
            if hasattr(self, "carrier_filter") and self.carrier_filter.text():
                if hasattr(current_tab, "filter_carriers"):
                    current_tab.filter_carriers(self.carrier_filter.text().lower(), filter_type="name")
            
            # Apply status filter if there is any
            if hasattr(current_tab, "handle_global_filter_click"):
                current_tab.handle_global_filter_click(self.current_status_filter)
            
            # Update stats
            if hasattr(current_tab, "update_stats"):
                current_tab.update_stats()

    def init_top_button_row(self):
        """Create a horizontal row for utility buttons.

        Contains:
        - Date Selection, Carrier List, and OTDL Maximization buttons
        - Global carrier filter textbox
        """
        # Create top button row
        button_row_layout = QHBoxLayout()

        # Create a container widget for the button row with a darker background
        button_container = QWidget()
        button_container.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                border-bottom: 1px solid #333333;
            }
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #E1E1E1;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: normal;
                text-align: left;
                margin: 8px 4px;
            }
            QPushButton:hover {
                background-color: #383838;
                border-color: #4D4D4D;
            }
            QLineEdit {
                background-color: #2D2D2D;
                color: #E1E1E1;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                margin: 8px 4px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border: 1px solid #BB86FC;
            }
            QLineEdit::placeholder {
                color: #808080;
            }
            """
        )

        # Create buttons with icons
        self.date_selection_button = QPushButton("  Date Selection")
        self.date_selection_button.setCheckable(True)
        self.date_selection_button.clicked.connect(self.toggle_date_selection_pane)

        self.carrier_list_button = QPushButton("  Carrier List")
        self.carrier_list_button.setCheckable(True)
        self.carrier_list_button.clicked.connect(self.toggle_carrier_list_pane)

        self.otdl_maximization_button = QPushButton("  OTDL Maximization")
        self.otdl_maximization_button.setCheckable(True)
        self.otdl_maximization_button.clicked.connect(self.toggle_otdl_maximization_pane)

        # Add global carrier filter
        self.carrier_filter = QLineEdit()
        self.carrier_filter.setPlaceholderText("Filter carriers across all tabs...")
        self.carrier_filter.textChanged.connect(self.on_carrier_filter_changed)

        # Add buttons and filter to layout
        button_row_layout.addWidget(self.date_selection_button)
        button_row_layout.addWidget(self.carrier_list_button)
        button_row_layout.addWidget(self.otdl_maximization_button)
        button_row_layout.addWidget(self.carrier_filter)
        button_row_layout.addStretch()

        button_container.setLayout(button_row_layout)
        self.main_layout.addWidget(button_container)

    def init_filter_button_row(self):
        """Create a horizontal row for filter buttons at the bottom.

        Contains:
        - Status filter buttons with carrier stats
        - Date range display
        """
        # Create filter row
        filter_row = QWidget()
        filter_row.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-top: 1px solid #333333;
            }
            QPushButton {
                background-color: rgba(187, 134, 252, 0.1);
                border: none;
                color: #BB86FC;
                padding: 4px 8px;
                font-size: 12px;
                margin: 2px;
                min-width: 90px;
                max-height: 24px;
                border-radius: 4px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(187, 134, 252, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(187, 134, 252, 0.3);
            }
            QPushButton:checked {
                background-color: #BB86FC;
                color: #000000;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
                padding: 4px 8px;
            }
        """)

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(8, 12, 8, 12)  # Added vertical padding
        filter_layout.setSpacing(4)  # Spacing between buttons

        # Create status filter buttons with stats
        self.total_btn = self.create_filter_button("Total Carriers: 0")
        self.wal_btn = self.create_filter_button("WAL: 0")
        self.nl_btn = self.create_filter_button("NL: 0")
        self.otdl_btn = self.create_filter_button("OTDL: 0")
        self.ptf_btn = self.create_filter_button("PTF: 0")
        self.violations_btn = self.create_filter_button("Carriers With Violations: 0")

        # Add buttons to layout
        for btn in [self.total_btn, self.wal_btn, self.nl_btn, self.otdl_btn, self.ptf_btn, self.violations_btn]:
            filter_layout.addWidget(btn)

        # Add date range label
        self.date_range_label = QLabel("Selected Date Range: ")
        self.date_range_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        filter_layout.addStretch()  # This pushes the date range to the right
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
        for btn in [self.total_btn, self.wal_btn, self.nl_btn, self.otdl_btn, self.ptf_btn, self.violations_btn]:
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
        """Update the filter button statistics.
        
        Args:
            total (int): Total number of carriers
            wal (int): Number of WAL carriers
            nl (int): Number of NL carriers
            otdl (int): Number of OTDL carriers
            ptf (int): Number of PTF carriers
            violations (int): Number of carriers with violations
        """
        self.total_btn.setText(f"Total Carriers: {total}")
        self.wal_btn.setText(f"WAL: {wal}")
        self.nl_btn.setText(f"NL: {nl}")
        self.otdl_btn.setText(f"OTDL: {otdl}")
        self.ptf_btn.setText(f"PTF: {ptf}")
        self.violations_btn.setText(f"Carriers With Violations: {violations}")

        # Force button update
        for btn in [self.total_btn, self.wal_btn, self.nl_btn, self.otdl_btn, self.ptf_btn, self.violations_btn]:
            btn.update()

    def apply_global_status_filter(self, status):
        """Apply the global status filter to all tabs.
        
        Args:
            status (str): The status to filter by ('all', 'wal', 'nl', etc.)
        """
        current_tab = self.central_tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, "handle_global_filter_click"):
            current_tab.handle_global_filter_click(status)
            current_tab.update_stats()

    def init_85d_tab(self):
        """Initialize the Article 8.5.D violation tab."""
        print("Initializing 8.5.D Violations Tab")  # Debugging statement

        """Initialize and add the 8.5.D Tab."""
        self.vio_85d_tab = Violation85dTab()
        self.central_tab_widget.addTab(self.vio_85d_tab, "8.5.D Violations")
        self.vio_85d_tab.refresh_data(pd.DataFrame())  # Start with an empty DataFrame

        # Connect tab change signal
        self.central_tab_widget.currentChanged.connect(self.handle_main_tab_change)

    def init_85f_tab(self):
        """Initialize the Article 8.5.F violation tab."""
        print("Initializing 8.5.F Violations Tab")  # Debugging statement

        """Initialize and add the 8.5.F Tab."""
        self.vio_85f_tab = Violation85fTab()
        self.central_tab_widget.addTab(self.vio_85f_tab, "8.5.F Violations")
        self.vio_85f_tab.initUI(pd.DataFrame())  # Start with an empty DataFrame

    def init_85f_ns_tab(self):
        """Initialize the Article 8.5.F non-scheduled day violation tab."""
        print("Initializing 8.5.F NS Violations Tab")  # Debugging statement

        """Initialize and add the 8.5.F NS Tab."""
        self.vio_85f_ns_tab = Violation85fNsTab()
        self.central_tab_widget.addTab(self.vio_85f_ns_tab, "8.5.F NS Violations")
        self.vio_85f_ns_tab.initUI(pd.DataFrame())  # Start with an empty DataFrame

    def init_85f_5th_tab(self):
        """Initialize the Article 8.5.F fifth overtime day violation tab."""
        print("Initializing 8.5.F 5th Violations Tab")  # Debugging statement

        """Initialize and add the 8.5.F 5th Tab."""
        self.vio_85f_5th_tab = Violation85f5thTab()
        self.central_tab_widget.addTab(self.vio_85f_5th_tab, "8.5.F 5th Violations")
        self.vio_85f_5th_tab.refresh_data(
            pd.DataFrame()
        )  # Start with an empty DataFrame

    def init_MAX12_tab(self):
        """Initialize the Maximum 12-Hour Rule violation tab.

        Creates and configures the tab for tracking violations of the 12-hour daily
        work limit. This includes setting up the tab widget, connecting signals,
        and configuring the display.
        """
        self.vio_MAX12_tab = ViolationMax12Tab(self)
        self.central_tab_widget.addTab(self.vio_MAX12_tab, "MAX12")

    def init_MAX60_tab(self):
        """Initialize the Maximum 60-Hour Rule violation tab.

        Creates and configures the tab for tracking violations of the 60-hour weekly
        work limit. This includes setting up the tab widget, connecting signals,
        and configuring the display.
        """
        self.vio_MAX60_tab = ViolationMax60Tab(self)
        self.central_tab_widget.addTab(self.vio_MAX60_tab, "MAX60")

    def init_remedies_tab(self):
        """Initialize the violation remedies summary tab."""
        print("Initializing Violations Summary Tab")  # Debugging statement

        """Initialize and add the Remedies Tab."""
        self.remedies_tab = ViolationRemediesTab()
        self.central_tab_widget.addTab(self.remedies_tab, "Violations Summary")
        self.remedies_tab.refresh_data(pd.DataFrame())  # Start with an empty DataFrame

    def apply_date_range(self):
        """Apply the selected date range and update all tabs."""
        if not os.path.exists("carrier_list.json"):
            response = CustomWarningDialog.warning(
                self,
                "Carrier List Required",
                "The carrier list needs to be configured and saved before processing dates.\n\n"
                "1. Configure your carrier list\n"
                "2. Click 'Save/Apply' to save your changes\n\n"
                "Would you like to open the Carrier List setup now?",
            )

            if response == QMessageBox.Yes:
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

        # Second check: Carrier List content validation
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
        progress = CustomProgressDialog(
            "Processing data...", "", 0, 100, self, title="Processing Date Range"
        )
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        progress.show()

        # Store reference to prevent garbage collection
        self.progress_dialog = progress

        try:
            # Ensure UI updates by processing events
            QApplication.processEvents()

            # Ensure the DateSelectionPane is initialized
            if (
                not hasattr(self, "date_selection_pane")
                or self.date_selection_pane is None
            ):
                QMessageBox.critical(
                    self, "Error", "Date Selection Pane is not initialized."
                )
                return

            # Access the calendar from the DateSelectionPane
            selected_date = self.date_selection_pane.calendar.selectedDate()
            if selected_date.dayOfWeek() != 6:  # Ensure the selected date is a Saturday
                QMessageBox.warning(
                    self,
                    "Invalid Date",
                    "Please select a Saturday."
                )
                return

            progress.setValue(20)
            progress.setLabelText("Clearing existing data...")
            QApplication.processEvents()

            progress.setValue(30)
            progress.setLabelText("Fetching clock ring data...")
            start_date = selected_date.toString("yyyy-MM-dd")
            end_date = selected_date.addDays(6).toString("yyyy-MM-dd")
            
            # Update the date range display
            self.update_date_range_display(start_date, end_date)
            
            clock_ring_data = self.fetch_clock_ring_data(start_date, end_date)

            progress.setValue(40)
            progress.setLabelText("Processing carrier list...")
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

            # Continue with the rest of the processing
            progress.setValue(60)
            progress.setLabelText("Initializing violation tabs...")
            self.vio_85d_tab.refresh_data(pd.DataFrame())
            self.vio_85f_tab.refresh_data(pd.DataFrame())
            self.vio_85f_ns_tab.refresh_data(pd.DataFrame())
            self.vio_85f_5th_tab.refresh_data(pd.DataFrame())
            self.vio_MAX12_tab.refresh_data(pd.DataFrame())
            self.vio_MAX60_tab.refresh_data(pd.DataFrame())
            self.remedies_tab.refresh_data(pd.DataFrame())

            progress.setValue(80)
            progress.setLabelText("Updating OTDL data...")
            if self.otdl_maximization_pane is None:
                self.otdl_maximization_pane = OTDLMaximizationPane(self)
            self.otdl_maximization_pane.refresh_data(clock_ring_data, clock_ring_data)

            progress.setValue(90)
            progress.setLabelText("Calculating violations...")
            self.update_violations_and_remedies(clock_ring_data)

            progress.setValue(100)
            self.statusBar().showMessage(
                "Date range processing complete", 5000
            )

        except Exception as e:
            progress.cancel()
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred: {str(e)}"
            )
        finally:
            # Clean up
            self.progress_dialog = None

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
                with open("carrier_list.json", "r") as json_file:
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
        self.vio_MAX12_tab = None
        self.vio_MAX60_tab = None
        self.remedies_tab = None

        # Reset other associated data
        self.current_data = pd.DataFrame()
        self.violations = None

    def auto_detect_klusterbox_path(self):
        """Auto-detect the Klusterbox database path.

        Searches for mandates.sqlite in:
        - Current directory
        - Common installation locations
        - User data directories

        Returns:
            str: Path to mandates.sqlite if found, None otherwise

        Note:
            - Handles both Windows and Unix-like systems
            - Validates database file existence
            - Returns None if database not found
        """
        if os.name == "nt":
            default_path = (
                os.path.expanduser("~") + "\\Documents\\.klusterbox\\mandates.sqlite"
            )
            if os.path.exists(default_path):
                return default_path
        return None

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

        # Exit menu entry
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addActions([exit_action])

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
            from settings_dialog import SettingsDialog

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

        # Explicitly connect the signal
        print("Connecting carrier list signal to OTDL pane...")
        self.carrier_list_pane.carrier_list_updated.connect(
            self.otdl_maximization_pane.handle_carrier_list_update
        )

        print("OTDL pane initialization complete")
        self.otdl_maximization_pane.hide()

    def handle_maximized_status_change(self, date, maximized_status):
        """Handle changes to OTDL maximization status"""
        if "8.5.D" not in self.violations:
            return

        # Update 8.5.D violations for the specified date
        violation_85d_data = self.violations["8.5.D"]
        date_mask = violation_85d_data["date"] == date

        if maximized_status:
            # Mark all 8.5.D violations for the date as maximized
            violation_85d_data.loc[
                date_mask, "violation_type"
            ] = "No Violation (OTDL Maxed)"
            violation_85d_data.loc[date_mask, "remedy_total"] = 0.00

            # Refresh the 8.5.D tab with updated data
            self.vio_85d_tab.refresh_data(violation_85d_data)

            # Update remedies data and refresh summary tabs
            remedies_data = get_violation_remedies(
                self.fetch_clock_ring_data(), self.violations
            )
            self.remedies_tab.refresh_data(remedies_data)
        else:
            # Redetect violations and update all related views
            clock_ring_data = self.fetch_clock_ring_data()
            if not clock_ring_data.empty:
                # Update violations
                self.violations["8.5.D"] = detect_violations(
                    clock_ring_data, "8.5.D Overtime Off Route"
                )
                # Refresh all affected tabs
                self.vio_85d_tab.refresh_data(self.violations["8.5.D"])
                remedies_data = get_violation_remedies(clock_ring_data, self.violations)
                self.remedies_tab.refresh_data(remedies_data)

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

    def update_violations_and_remedies(self, clock_ring_data=None):
        """Helper function to detect violations and update all tabs."""
        if clock_ring_data is None or clock_ring_data.empty:
            return

        # Define violation types
        violation_types = {
            "8.5.D": "8.5.D Overtime Off Route",
            "8.5.F": "8.5.F Overtime Over 10 Hours Off Route",
            "8.5.F NS": "8.5.F NS Overtime On a Non-Scheduled Day",
            "8.5.F 5th": "8.5.F 5th More Than 4 Days of Overtime in a Week",
            "MAX12": "MAX12 More Than 12 Hours Worked in a Day",
            "MAX60": "MAX60 More Than 60 Hours Worked in a Week",
        }

        # Detect violations
        self.violations = {}
        for key, violation_type in violation_types.items():
            self.violations[key] = detect_violations(clock_ring_data, violation_type)

        # Update violation tabs
        self.vio_85d_tab.refresh_data(self.violations["8.5.D"])
        self.vio_85f_tab.refresh_data(self.violations["8.5.F"])
        self.vio_85f_ns_tab.refresh_data(self.violations["8.5.F NS"])
        self.vio_85f_5th_tab.refresh_data(self.violations["8.5.F 5th"])
        self.vio_MAX12_tab.refresh_data(self.violations["MAX12"])
        self.vio_MAX60_tab.refresh_data(self.violations["MAX60"])

        # Calculate and update remedies
        remedies_data = get_violation_remedies(clock_ring_data, self.violations)
        self.remedies_tab.refresh_data(remedies_data)

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
        """Fetch clock ring data for the selected date range from mandates.sqlite.

        Retrieves clock ring data and fills missing entries using pandas.
        """
        query = """
        SELECT
            r.carrier_name,
            DATE(r.rings_date) AS rings_date,
            c.list_status,
            c.station,
            r.total,
            r.moves,
            r.code,
            r.leave_type,
            r.leave_time
        FROM rings3 r
        JOIN (
            SELECT carrier_name, list_status, station
            FROM carriers
            WHERE (carrier_name, effective_date) IN (
                SELECT carrier_name, MAX(effective_date)
                FROM carriers
                GROUP BY carrier_name
            )
        ) c ON r.carrier_name = c.carrier_name
        WHERE r.rings_date BETWEEN ? AND ?
        """
        try:
            # Validate the date_selection_pane and calendar
            if (
                not hasattr(self, "date_selection_pane")
                or self.date_selection_pane is None
            ):
                raise AttributeError("Date selection pane is not initialized.")

            if (
                not hasattr(self.date_selection_pane, "calendar")
                or self.date_selection_pane.calendar is None
            ):
                raise AttributeError("Calendar widget is not initialized.")

            # Get the selected date from the calendar
            selected_date = self.date_selection_pane.calendar.selectedDate()
            if not selected_date.isValid():
                raise ValueError("No valid date selected in the calendar.")

            start_date = selected_date.toString("yyyy-MM-dd")
            end_date = selected_date.addDays(7).toString("yyyy-MM-dd")

            with sqlite3.connect(self.mandates_db_path) as conn:
                db_data = pd.read_sql_query(query, conn, params=(start_date, end_date))

                # Filter out carriers with "out of station"
                db_data = db_data[
                    ~db_data["station"].str.contains(
                        "out of station", case=False, na=False
                    )
                ]

                # Convert rings_date to string format (YYYY-MM-DD)
                db_data["rings_date"] = pd.to_datetime(
                    db_data["rings_date"]
                ).dt.strftime("%Y-%m-%d")

                # Convert 'total' to numeric explicitly
                db_data["total"] = pd.to_numeric(
                    db_data["total"], errors="coerce"
                ).fillna(0)

                # Load the current carrier list from JSON
                try:
                    with open("carrier_list.json", "r") as json_file:
                        carrier_list_df = pd.DataFrame(json.load(json_file))

                    # Create a mapping of carrier names to their current list status
                    carrier_status_map = carrier_list_df.set_index("carrier_name")[
                        "list_status"
                    ].to_dict()

                    # Update list_status in db_data based on the JSON file
                    db_data["list_status"] = (
                        db_data["carrier_name"]
                        .map(carrier_status_map)
                        .fillna(db_data["list_status"])
                    )

                    # Get the full list of carriers from the JSON file
                    carrier_names = carrier_list_df["carrier_name"].unique()
                except (FileNotFoundError, json.JSONDecodeError):
                    carrier_names = db_data["carrier_name"].unique()
                    print(
                        "Warning: Could not load carrier_list.json, using database carriers only"
                    )

                # Create all date combinations
                all_dates = pd.date_range(
                    start=start_date, end=end_date, inclusive="left"
                )
                all_combinations = pd.MultiIndex.from_product(
                    [carrier_names, all_dates], names=["carrier_name", "rings_date"]
                )

                # Reindex to include all carrier-date combinations
                db_data["rings_date"] = pd.to_datetime(db_data["rings_date"])
                db_data = db_data.set_index(["carrier_name", "rings_date"])
                db_data = db_data.reindex(all_combinations, fill_value=0).reset_index()

                # Convert reindexed rings_date back to string
                db_data["rings_date"] = db_data["rings_date"].dt.strftime("%Y-%m-%d")

                # Add the display_indicators column
                db_data["display_indicators"] = db_data.apply(set_display, axis=1)

                # Drop the station column to maintain the original structure
                db_data.drop(columns=["station"], inplace=True)

                return db_data

        except (AttributeError, ValueError) as e:
            QMessageBox.critical(self, "Calendar Error", str(e))
            return pd.DataFrame(
                columns=[
                    "carrier_name",
                    "rings_date",
                    "list_status",
                    "total",
                    "moves",
                    "code",
                    "leave_type",
                    "display_indicators",
                ]
            )

        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return pd.DataFrame(
                columns=[
                    "carrier_name",
                    "rings_date",
                    "list_status",
                    "total",
                    "moves",
                    "code",
                    "leave_type",
                    "display_indicators",
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
                self,
                "Error",
                f"Failed to load carrier data: {str(e)}"
            )

    def export_violations(self):
        """Export violations to Excel."""
        try:
            self.remedies_tab.export_to_excel()
            QMessageBox.information(
                self,
                "Success",
                "Violations exported successfully"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export violations: {str(e)}"
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
            self.settings_dialog.activateWindow()

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
        elif violation_type == "8.5.F":
            return self.vio_85f_tab
        elif violation_type == "8.5.F NS":
            return self.vio_85f_ns_tab
        elif violation_type == "8.5.F 5th":
            return self.vio_85f_5th_tab
        elif violation_type == "MAX12":
            return self.vio_MAX12_tab
        elif violation_type == "MAX60":
            return self.vio_MAX60_tab
        elif violation_type == "Summary":
            return self.remedies_tab
        else:
            return None

    def apply_global_carrier_filter(self, text):
        """Apply carrier filter text across all violation tabs.

        Args:
            text (str): The filter text to apply
        """
        # Apply filter to each violation tab
        for tab in [
            self.vio_85d_tab,
            self.vio_85f_tab,
            self.vio_85f_ns_tab,
            self.vio_85f_5th_tab,
            self.vio_MAX12_tab,
            self.vio_MAX60_tab,
            self.remedies_tab,
        ]:
            if hasattr(tab, "filter_carriers"):
                tab.filter_carriers(text, "name")

    def apply_global_status_filter(self, status_type):
        """Apply status filter across all violation tabs.

        Args:
            status_type (str): The status to filter by ('all', 'wal', 'nl', 'otdl', 'ptf', 'violations')
        """
        # Store current filter state
        self.current_status_filter = status_type

        # Apply filter to each violation tab
        for tab in [
            self.vio_85d_tab,
            self.vio_85f_tab,
            self.vio_85f_ns_tab,
            self.vio_85f_5th_tab,
            self.vio_MAX12_tab,
            self.vio_MAX60_tab,
            self.remedies_tab,
        ]:
            if hasattr(tab, "handle_global_filter_click"):
                tab.handle_global_filter_click(status_type)
                # Force stats update after applying filter
                tab.update_stats()

    def toggle_date_selection_pane(self):
        """Toggle the Date Selection Pane and button state."""
        if not hasattr(self, "date_selection_pane") or self.date_selection_pane is None:
            self.date_selection_pane = DateSelectionPane(self)

        if self.date_selection_pane.isVisible():
            self.date_selection_pane.hide()
            self.date_selection_button.setChecked(False)
        else:
            self.date_selection_pane.show()
            self.date_selection_button.setChecked(True)

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
        if not hasattr(self, "otdl_maximization_pane") or self.otdl_maximization_pane is None:
            self.otdl_maximization_pane = OTDLMaximizationPane(self.carrier_list_pane, self)

        if self.otdl_maximization_pane.isVisible():
            self.otdl_maximization_pane.hide()
            self.otdl_maximization_button.setChecked(False)
        else:
            self.otdl_maximization_pane.show()
            self.otdl_maximization_pane.setMinimumSize(1053, 681)
            self.otdl_maximization_button.setChecked(True)

    def handle_status_filter_click(self, status):
        """Handle clicks on status filter buttons.
        
        Args:
            status (str): The status filter to apply ('WAL', 'NL', etc.)
        """
        # Store current filter
        self.current_status_filter = status

        # Uncheck all buttons except the clicked one
        for button in [self.wal_button, self.nl_button, self.wal_nl_button, 
                      self.otdl_button, self.aux_button, self.all_button]:
            if button.text() == status:
                button.setChecked(True)
            else:
                button.setChecked(False)

        # Get current tab and apply filter if it supports it
        current_tab = self.central_tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, "handle_global_filter_click"):
            current_tab.handle_global_filter_click(status)
            current_tab.update_stats()

    def on_carrier_filter_changed(self, text):
        """Handle changes to the carrier filter text.
        
        Args:
            text (str): The new filter text
        """
        # Get current tab and apply filter if it supports it
        current_tab = self.central_tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, "filter_carriers"):
            current_tab.filter_carriers(text.lower(), filter_type="name")

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
        if hasattr(self, 'date_range_label'):
            self.date_range_label.setText(f"Selected Date Range: {start_date} to {end_date}")


if __name__ == "__main__":
    # Run the application
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()

    # Run the event loop
    exit_code = app.exec_()

    # Exit the program
    sys.exit(exit_code)
