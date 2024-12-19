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
import pandas as pd

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

        # Add sync button
        sync_button = QPushButton("Sync Database")
        sync_button.clicked.connect(self.sync_database)
        button_layout.addWidget(sync_button)

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

    def sync_database(self):
        """Synchronize the working database with the source database."""
        try:
            # Get target database path
            target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eightbox.sqlite")
            source_path = self.mandates_db_path
            
            print(f"\nStarting sync process...")
            print(f"Source: {source_path}")
            print(f"Target: {target_path}")
            
            # Connect to both databases
            source_conn = sqlite3.connect(source_path)
            target_conn = sqlite3.connect(target_path)
            
            try:
                # Start transaction
                target_conn.execute("BEGIN TRANSACTION")
                
                # Add diagnostic queries
                print("\nDiagnostic Information:")
                
                # Get total counts from both databases
                source_cursor = source_conn.cursor()
                target_cursor = target_conn.cursor()
                
                source_cursor.execute("SELECT COUNT(*) FROM rings3")
                target_cursor.execute("SELECT COUNT(*) FROM rings3")
                source_count = source_cursor.fetchone()[0]
                target_count = target_cursor.fetchone()[0]
                print(f"Total records in source rings3: {source_count}")
                print(f"Total records in target rings3: {target_count}")
                
                # Get the latest records from both databases
                print("\nLatest records in source rings3:")
                source_cursor.execute("""
                    SELECT rings_date, carrier_name, total 
                    FROM rings3 
                    ORDER BY rings_date DESC, carrier_name 
                    LIMIT 5
                """)
                for row in source_cursor.fetchall():
                    print(f"Date: {row[0]}, Carrier: {row[1]}, Total: {row[2]}")
                    
                print("\nLatest records in target rings3:")
                target_cursor.execute("""
                    SELECT rings_date, carrier_name, total 
                    FROM rings3 
                    ORDER BY rings_date DESC, carrier_name 
                    LIMIT 5
                """)
                for row in target_cursor.fetchall():
                    print(f"Date: {row[0]}, Carrier: {row[1]}, Total: {row[2]}")
                
                stats = {"rings3_added": 0, "carriers_added": 0, "carriers_modified": 0}
                
                # Get only new records that don't exist in the target
                print("\nChecking for new records...")
                
                # Get all records from source
                source_cursor.execute("""
                    SELECT DISTINCT s.* 
                    FROM rings3 s 
                    ORDER BY s.rings_date DESC, s.carrier_name
                """)
                source_records = source_cursor.fetchall()
                
                # Check each source record against target
                new_records = []
                for record in source_records:
                    rings_date, carrier_name = record[0], record[1]
                    target_cursor.execute("""
                        SELECT 1 FROM rings3 
                        WHERE rings_date = ? 
                        AND carrier_name = ?
                    """, (rings_date, carrier_name))
                    
                    if not target_cursor.fetchone():
                        new_records.append(record)
                        print(f"Found new record: Date: {rings_date}, Carrier: {carrier_name}")
                
                if new_records:
                    print(f"\nPreparing to add {len(new_records)} records:")
                    for record in new_records[:5]:  # Show first 5 records
                        print(record)
                    
                    # Insert new records directly
                    target_conn.executemany("""
                        INSERT INTO rings3 (
                            rings_date, carrier_name, total, rs, code, moves,
                            leave_type, leave_time, refusals, bt, et
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, new_records)
                    stats["rings3_added"] = len(new_records)

                # Handle carriers table similarly - using direct SQL like rings3
                print("\nChecking for new carrier records...")
                source_cursor.execute("""
                    SELECT DISTINCT s.* 
                    FROM carriers s 
                    ORDER BY s.effective_date DESC, s.carrier_name
                """)
                source_carrier_records = source_cursor.fetchall()
                
                # Check each source carrier record against target
                new_carrier_records = []
                for record in source_carrier_records:
                    effective_date, carrier_name = record[0], record[1]
                    target_cursor.execute("""
                        SELECT 1 FROM carriers 
                        WHERE effective_date = ? 
                        AND carrier_name = ?
                    """, (effective_date, carrier_name))
                    
                    if not target_cursor.fetchone():
                        new_carrier_records.append(record)
                        print(f"Found new carrier record: Date: {effective_date}, Carrier: {carrier_name}")
                
                if new_carrier_records:
                    print(f"\nPreparing to add {len(new_carrier_records)} carrier records:")
                    for record in new_carrier_records[:5]:  # Show first 5 records
                        print(record)
                    
                    # Insert new carrier records directly
                    target_conn.executemany("""
                        INSERT INTO carriers (
                            effective_date, carrier_name, list_status,
                            ns_day, route_s, station
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, new_carrier_records)
                    stats["carriers_added"] = len(new_carrier_records)

                # Check for modified carrier records
                modified_carriers = pd.read_sql_query("""
                    SELECT s.* 
                    FROM carriers s
                    JOIN carriers t ON 
                        s.effective_date = t.effective_date AND
                        s.carrier_name = t.carrier_name
                    WHERE COALESCE(s.list_status,'') != COALESCE(t.list_status,'')
                       OR COALESCE(s.ns_day,'') != COALESCE(t.ns_day,'')
                       OR COALESCE(s.route_s,'') != COALESCE(t.route_s,'')
                       OR COALESCE(s.station,'') != COALESCE(t.station,'')
                """, source_conn)

                if not modified_carriers.empty:
                    print(f"\nUpdating {len(modified_carriers)} modified carrier records")
                    
                    # Update modified records
                    for _, record in modified_carriers.iterrows():
                        target_conn.execute("""
                            UPDATE carriers 
                            SET list_status = ?, ns_day = ?, route_s = ?, station = ?
                            WHERE effective_date = ? AND carrier_name = ?
                        """, (
                            record['list_status'], record['ns_day'], 
                            record['route_s'], record['station'],
                            record['effective_date'], record['carrier_name']
                        ))
                    stats["carriers_modified"] = len(modified_carriers)

                # If we added any records, update the sync log
                if stats["rings3_added"] > 0 or stats["carriers_added"] > 0 or stats["carriers_modified"] > 0:
                    from datetime import datetime
                    now = datetime.now().isoformat()
                    target_conn.execute("""
                        INSERT INTO sync_log (
                            sync_date, 
                            rows_added_rings3, 
                            rows_added_carriers
                        ) VALUES (?, ?, ?)
                    """, (now, stats["rings3_added"], stats["carriers_added"]))
                    
                    target_conn.commit()
                    print("\nSync completed successfully!")
                    message = (
                        f"Sync completed successfully.\n"
                        f"Added {stats['rings3_added']} new clock rings\n"
                        f"Added {stats['carriers_added']} new carrier records\n"
                        f"Updated {stats['carriers_modified']} carrier records"
                    )
                    CustomWarningDialog.warning(self, "Sync Complete", message)
                    return True, message, stats
                else:
                    target_conn.rollback()
                    print("\nNo new records to add - databases are in sync")
                    CustomWarningDialog.warning(self, "Sync Complete", "No new records to sync")
                    return False, "No new records to sync", stats
                    
            except Exception as e:
                target_conn.rollback()
                print(f"\nError during sync operation: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                raise e
                
            finally:
                source_conn.close()
                target_conn.close()
                
        except Exception as e:
            print(f"\nFatal sync error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            CustomWarningDialog.warning(
                self,
                "Sync Error",
                f"An error occurred during sync:\n{str(e)}"
            )
            return False, f"Sync failed: {str(e)}", None
