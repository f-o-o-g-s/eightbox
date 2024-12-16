"""Dialog for configuring application settings.

This module provides a dialog interface for users to:
- Configure application preferences
- Set default values and behaviors
- Customize UI settings
- Manage data paths and locations
- Save/load configuration
"""

import os
import sqlite3

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    CustomTitleBarWidget,
    CustomWarningDialog,
)


class SettingsDialog(QDialog):
    """Dialog interface for application settings and configuration.

    Provides a user interface for viewing and modifying application settings,
    including database connections and user preferences.
    """

    # Signal emitted when database path changes and is validated
    pathChanged = pyqtSignal(str)

    def __init__(self, current_path, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mandates_db_path = current_path
        self.drag_pos = None

        # Set window flags for frameless window
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar with dragging enabled
        self.title_bar = CustomTitleBarWidget(title="Settings", parent=self)
        layout.addWidget(self.title_bar)

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Labels
        path_label = QLabel("Current Database Path")
        path_label.setStyleSheet("font-size: 12px; font-weight: bold;")

        self.path_display = QLabel(self.mandates_db_path)
        self.path_display.setStyleSheet(
            """
            color: #9575CD;
            font-size: 11px;
            padding: 5px;
        """
        )
        self.path_display.setWordWrap(True)
        self.path_display.setMinimumWidth(360)

        status_label = QLabel("Status")
        status_label.setStyleSheet("font-size: 12px; font-weight: bold;")

        self.status_display = QLabel("Connected ✓")
        self.status_display.setStyleSheet(
            """
            color: #81C784;
            font-size: 11px;
            padding: 5px;
        """
        )

        # Button container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Check for auto-detected path
        auto_detected_path = None
        if hasattr(self.parent, "auto_detect_klusterbox_path"):
            auto_detected_path = self.parent.auto_detect_klusterbox_path()

        # Add auto-detect button if available and not currently using it
        if auto_detected_path and auto_detected_path != self.mandates_db_path:
            use_auto_detect_button = QPushButton("Use Auto-detected Klusterbox Path")
            use_auto_detect_button.clicked.connect(
                lambda: self.use_auto_detected_path(auto_detected_path)
            )
            button_layout.addWidget(use_auto_detect_button)

        set_path_button = QPushButton("Set Database Path")
        set_path_button.clicked.connect(self.set_database_path)
        button_layout.addWidget(set_path_button)

        save_button = QPushButton("Save and Close")
        save_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(save_button)

        # Add widgets to content layout
        content_layout.addWidget(path_label)
        content_layout.addWidget(self.path_display)
        content_layout.addSpacing(10)
        content_layout.addWidget(status_label)
        content_layout.addWidget(self.status_display)
        content_layout.addSpacing(20)
        content_layout.addWidget(button_container, alignment=Qt.AlignCenter)
        content_layout.addStretch()

        # Add content widget to main layout
        layout.addWidget(content_widget)

        # Set minimum size
        self.setMinimumSize(450, 400)
        self.adjustSize()

    def mouse_press_event(self, event):
        """Handle mouse press events for window dragging."""
        self.drag_pos = event.globalPos()

    def mouse_move_event(self, event):
        """Handle mouse move events for window dragging."""
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()

    def mouse_release_event(self):
        """Handle mouse release events for window dragging."""
        self.drag_pos = None

    def validate_database(self, path):
        """Validate that the given path points to a valid SQLite database.

        Args:
            path (str): Path to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(path):
            self.update_status("Error: Database file not found", error=True)
            return False

        try:
            # Attempt to connect to the database
            conn = sqlite3.connect(path)

            # Check for required tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            required_tables = {"rings3", "carriers"}
            if not required_tables.issubset(tables):
                missing = required_tables - tables
                self.update_status(
                    f"Error: Missing tables: {', '.join(missing)}", error=True
                )
                conn.close()
                return False

            conn.close()
            self.update_status("Connected ✓")
            return True

        except sqlite3.Error as e:
            self.update_status(f"Error: Invalid database - {str(e)}", error=True)
            return False
        except Exception as e:
            self.update_status(f"Error: {str(e)}", error=True)
            return False

    def update_status(self, message, error=False):
        """Update the status display with a message.

        Args:
            message (str): Status message to display
            error (bool): Whether this is an error message
        """
        self.status_display.setText(message)
        if error:
            self.status_display.setStyleSheet(
                """
                color: #EF5350;
                font-size: 11px;
                padding: 5px;
            """
            )
        else:
            self.status_display.setStyleSheet(
                """
                color: #81C784;
                font-size: 11px;
                padding: 5px;
            """
            )

    def use_auto_detected_path(self, path):
        """Use the auto-detected Klusterbox database path.

        Args:
            path (str): The auto-detected path to use
        """
        if self.validate_database(path):
            self.mandates_db_path = path
            self.path_display.setText(self.mandates_db_path)
            self.update_status("Using auto-detected Klusterbox path")
        else:
            CustomWarningDialog.warning(
                self,
                "Invalid Database",
                "The auto-detected database is not valid.\n"
                "Please select a valid database file manually.",
            )

    def set_database_path(self):
        """Open file dialog to select and set new database path."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            "",
            "SQLite Database (*.sqlite);;All Files (*.*)",
        )

        if file_path:
            # Validate the selected database
            if self.validate_database(file_path):
                self.mandates_db_path = file_path
                self.path_display.setText(self.mandates_db_path)
            else:
                CustomWarningDialog.warning(
                    self,
                    "Invalid Database",
                    "The selected file is not a valid Klusterbox database.\n"
                    "Please select a valid database file.",
                )

    def apply_settings(self):
        """Apply and save the current settings."""
        if self.validate_database(self.mandates_db_path):
            # Emit the pathChanged signal with the new path
            self.pathChanged.emit(self.mandates_db_path)
            self.hide()
        else:
            CustomWarningDialog.warning(
                self,
                "Invalid Database",
                "Cannot save settings with an invalid database path.\n"
                "Please select a valid database file.",
            )
