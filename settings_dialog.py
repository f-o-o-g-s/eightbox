"""Dialog for configuring application settings.

This module provides a dialog interface for users to:
- View database status
- Sync databases
- Configure application preferences
"""

import os
import sqlite3

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    CustomInfoDialog,
    CustomTitleBarWidget,
    CustomWarningDialog,
)


class SettingsDialog(QDialog):
    """Dialog interface for application settings and configuration.

    Provides a user interface for viewing database status and syncing data.
    """

    def __init__(self, current_path, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mandates_db_path = current_path
        self.drag_pos = None
        self.eightbox_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "eightbox.sqlite"
        )

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

        # Klusterbox Database Section
        klusterbox_section = QWidget()
        klusterbox_layout = QVBoxLayout(klusterbox_section)
        klusterbox_layout.setSpacing(5)

        klusterbox_header = QLabel("Klusterbox Database (Source)")
        klusterbox_header.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #BB86FC;"
        )

        klusterbox_desc = QLabel(
            "The source database from Klusterbox containing carrier and clock ring data."
        )
        klusterbox_desc.setStyleSheet("font-size: 11px; color: #9E9E9E;")
        klusterbox_desc.setWordWrap(True)

        self.klusterbox_path_display = QLabel(self.mandates_db_path)
        self.klusterbox_path_display.setStyleSheet(
            """
            color: #9575CD;
            font-size: 11px;
            padding: 5px;
            background-color: #1E1E1E;
            border-radius: 4px;
        """
        )
        self.klusterbox_path_display.setWordWrap(True)
        self.klusterbox_path_display.setMinimumWidth(360)

        self.klusterbox_status = QLabel("Connected ✓")
        self.klusterbox_status.setStyleSheet(
            """
            color: #81C784;
            font-size: 11px;
            padding: 5px;
        """
        )

        klusterbox_layout.addWidget(klusterbox_header)
        klusterbox_layout.addWidget(klusterbox_desc)
        klusterbox_layout.addWidget(self.klusterbox_path_display)
        klusterbox_layout.addWidget(self.klusterbox_status)

        # Eightbox Database Section
        eightbox_section = QWidget()
        eightbox_layout = QVBoxLayout(eightbox_section)
        eightbox_layout.setSpacing(5)

        eightbox_header = QLabel("Eightbox Database (Working)")
        eightbox_header.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #BB86FC;"
        )

        eightbox_desc = QLabel(
            "The local working database used by Eightbox to store synchronized data."
        )
        eightbox_desc.setStyleSheet("font-size: 11px; color: #9E9E9E;")
        eightbox_desc.setWordWrap(True)

        self.eightbox_path_display = QLabel(self.eightbox_db_path)
        self.eightbox_path_display.setStyleSheet(
            """
            color: #9575CD;
            font-size: 11px;
            padding: 5px;
            background-color: #1E1E1E;
            border-radius: 4px;
        """
        )
        self.eightbox_path_display.setWordWrap(True)
        self.eightbox_path_display.setMinimumWidth(360)

        self.eightbox_status = QLabel("Initialized ✓")
        self.eightbox_status.setStyleSheet(
            """
            color: #81C784;
            font-size: 11px;
            padding: 5px;
        """
        )

        eightbox_layout.addWidget(eightbox_header)
        eightbox_layout.addWidget(eightbox_desc)
        eightbox_layout.addWidget(self.eightbox_path_display)
        eightbox_layout.addWidget(self.eightbox_status)

        # Button container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Add sync button
        sync_button = QPushButton("Sync Database")
        sync_button.clicked.connect(self.sync_database)
        button_layout.addWidget(sync_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide)
        button_layout.addWidget(close_button)

        # Add sections to content layout
        content_layout.addWidget(klusterbox_section)
        content_layout.addSpacing(20)
        content_layout.addWidget(eightbox_section)
        content_layout.addSpacing(20)
        content_layout.addWidget(button_container, alignment=Qt.AlignCenter)
        content_layout.addStretch()

        # Add content widget to main layout
        layout.addWidget(content_widget)

        # Set minimum size
        self.setMinimumSize(500, 600)
        self.adjustSize()

        # Update initial status
        self.validate_database(self.mandates_db_path)
        self.validate_eightbox_database()

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

    def validate_eightbox_database(self):
        """Validate the Eightbox database and update its status."""
        if not os.path.exists(self.eightbox_db_path):
            self.update_eightbox_status("Not initialized", error=True)
            return False

        try:
            conn = sqlite3.connect(self.eightbox_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            required_tables = {"rings3", "carriers", "sync_log"}

            if not required_tables.issubset(tables):
                missing = required_tables - tables
                self.update_eightbox_status(
                    f"Missing tables: {', '.join(missing)}", error=True
                )
                conn.close()
                return False

            # Get record counts
            cursor.execute("SELECT COUNT(*) FROM rings3")
            rings_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT carrier_name) FROM carriers")
            carriers_count = cursor.fetchone()[0]

            conn.close()
            self.update_eightbox_status(
                f"Initialized ✓ ({rings_count} rings, {carriers_count} unique carrier names)"
            )
            return True

        except sqlite3.Error as e:
            self.update_eightbox_status(f"Database error: {str(e)}", error=True)
            return False
        except Exception as e:
            self.update_eightbox_status(f"Error: {str(e)}", error=True)
            return False

    def validate_database(self, path):
        """Validate that the given path points to a valid SQLite database.

        Args:
            path (str): Path to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(path):
            self.update_klusterbox_status("Database file not found", error=True)
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
                self.update_klusterbox_status(
                    f"Missing tables: {', '.join(missing)}", error=True
                )
                conn.close()
                return False

            # Get record counts
            cursor.execute("SELECT COUNT(*) FROM rings3")
            rings_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT carrier_name) FROM carriers")
            carriers_count = cursor.fetchone()[0]

            conn.close()
            self.update_klusterbox_status(
                f"Connected ✓ ({rings_count} rings, {carriers_count} unique carrier names)"
            )
            return True

        except sqlite3.Error as e:
            self.update_klusterbox_status(f"Invalid database: {str(e)}", error=True)
            return False
        except Exception as e:
            self.update_klusterbox_status(f"Error: {str(e)}", error=True)
            return False

    def update_klusterbox_status(self, message, error=False):
        """Update the Klusterbox database status display.

        Args:
            message (str): Status message to display
            error (bool): Whether this is an error message
        """
        self.klusterbox_status.setText(message)
        if error:
            self.klusterbox_status.setStyleSheet(
                """
                color: #EF5350;
                font-size: 11px;
                padding: 5px;
            """
            )
        else:
            self.klusterbox_status.setStyleSheet(
                """
                color: #81C784;
                font-size: 11px;
                padding: 5px;
            """
            )

    def update_eightbox_status(self, message, error=False):
        """Update the Eightbox database status display.

        Args:
            message (str): Status message to display
            error (bool): Whether this is an error message
        """
        self.eightbox_status.setText(message)
        if error:
            self.eightbox_status.setStyleSheet(
                """
                color: #EF5350;
                font-size: 11px;
                padding: 5px;
            """
            )
        else:
            self.eightbox_status.setStyleSheet(
                """
                color: #81C784;
                font-size: 11px;
                padding: 5px;
            """
            )

    def sync_database(self):
        """Synchronize the working database with the source database."""
        try:
            # Get target database path
            target_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "eightbox.sqlite"
            )
            source_path = self.mandates_db_path

            print("Starting sync process...")
            print(f"Source: {source_path}")
            print(f"Target: {target_path}")

            # Check if target database exists and is initialized
            if not os.path.exists(target_path):
                print("Target database does not exist. Creating and initializing...")
                conn = sqlite3.connect(target_path)
                cursor = conn.cursor()

                # Create required tables
                cursor.execute(
                    """
                    CREATE TABLE carriers (
                        effective_date date,
                        carrier_name varchar,
                        list_status varchar,
                        ns_day varchar,
                        route_s varchar,
                        station varchar
                    )
                """
                )

                cursor.execute(
                    """
                    CREATE TABLE rings3 (
                        rings_date date,
                        carrier_name varchar,
                        total varchar,
                        rs varchar,
                        code varchar,
                        moves varchar,
                        leave_type varchar,
                        leave_time varchar,
                        refusals varchar,
                        bt varchar,
                        et varchar
                    )
                """
                )

                cursor.execute(
                    """
                    CREATE TABLE sync_log (
                        sync_date TEXT NOT NULL,
                        rows_added_rings3 INTEGER,
                        rows_added_carriers INTEGER,
                        backup_path TEXT
                    )
                """
                )

                # Create recommended indexes
                cursor.execute("CREATE INDEX idx_rings3_date ON rings3(rings_date)")
                cursor.execute(
                    "CREATE INDEX idx_carrier_name ON carriers(carrier_name)"
                )
                cursor.execute(
                    "CREATE INDEX idx_rings3_carrier_date ON rings3(carrier_name, rings_date)"
                )

                conn.commit()
                conn.close()
                print("Database initialized successfully.")

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
                source_cursor.execute(
                    """
                    SELECT rings_date, carrier_name, total
                    FROM rings3
                    ORDER BY rings_date DESC, carrier_name
                    LIMIT 5
                """
                )
                for row in source_cursor.fetchall():
                    print(f"Date: {row[0]}, Carrier: {row[1]}, Total: {row[2]}")

                print("\nLatest records in target rings3:")
                target_cursor.execute(
                    """
                    SELECT rings_date, carrier_name, total
                    FROM rings3
                    ORDER BY rings_date DESC, carrier_name
                    LIMIT 5
                """
                )
                for row in target_cursor.fetchall():
                    print(f"Date: {row[0]}, Carrier: {row[1]}, Total: {row[2]}")

                stats = {"rings3_added": 0, "carriers_added": 0, "carriers_modified": 0}

                # Get only new records that don't exist in the target
                print("Checking for new records...")

                # Get all records from source
                source_cursor.execute(
                    """
                    SELECT DISTINCT s.*
                    FROM rings3 s
                    ORDER BY s.rings_date DESC, s.carrier_name
                """
                )
                source_records = source_cursor.fetchall()

                # Check each source record against target
                new_records = []
                for record in source_records:
                    rings_date, carrier_name = record[0], record[1]
                    target_cursor.execute(
                        """
                        SELECT 1 FROM rings3
                        WHERE rings_date = ?
                        AND carrier_name = ?
                    """,
                        (rings_date, carrier_name),
                    )

                    if not target_cursor.fetchone():
                        new_records.append(record)
                        print(
                            f"Found new record: Date: {rings_date}, "
                            f"Carrier: {carrier_name}"
                        )

                if new_records:
                    print(f"Preparing to add {len(new_records)} records:")
                    for record in new_records[:5]:  # Show first 5 records
                        print(record)

                    # Insert new records directly
                    target_conn.executemany(
                        """
                        INSERT INTO rings3 (
                            rings_date, carrier_name, total, rs, code,
                            moves, leave_type, leave_time, refusals, bt, et
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        new_records,
                    )
                    stats["rings3_added"] = len(new_records)

                # Handle carriers table similarly - using direct SQL like rings3
                print("Checking for new carrier records...")
                source_cursor.execute(
                    """
                    SELECT DISTINCT s.*
                    FROM carriers s
                    ORDER BY s.effective_date DESC, s.carrier_name
                """
                )
                source_carrier_records = source_cursor.fetchall()

                # Check each source carrier record against target
                new_carrier_records = []
                for record in source_carrier_records:
                    effective_date, carrier_name = record[0], record[1]
                    target_cursor.execute(
                        """
                        SELECT 1 FROM carriers
                        WHERE effective_date = ?
                        AND carrier_name = ?
                    """,
                        (effective_date, carrier_name),
                    )

                    if not target_cursor.fetchone():
                        new_carrier_records.append(record)
                        print(
                            f"Found new carrier record: Date: {effective_date}, "
                            f"Carrier: {carrier_name}"
                        )

                if new_carrier_records:
                    print(
                        f"Preparing to add {len(new_carrier_records)} carrier records:"
                    )
                    for record in new_carrier_records[:5]:  # Show first 5 records
                        print(record)

                    # Insert new carrier records directly
                    target_conn.executemany(
                        """
                        INSERT INTO carriers (
                            effective_date, carrier_name, list_status,
                            ns_day, route_s, station
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        new_carrier_records,
                    )
                    stats["carriers_added"] = len(new_carrier_records)

                # Check for modified carrier records
                modified_carriers = pd.read_sql_query(
                    """
                    SELECT s.*
                    FROM carriers s
                    JOIN carriers t ON
                        s.effective_date = t.effective_date AND
                        s.carrier_name = t.carrier_name
                    WHERE COALESCE(s.list_status,'') != COALESCE(t.list_status,'')
                       OR COALESCE(s.ns_day,'') != COALESCE(t.ns_day,'')
                       OR COALESCE(s.route_s,'') != COALESCE(t.route_s,'')
                       OR COALESCE(s.station,'') != COALESCE(t.station,'')
                """,
                    source_conn,
                )

                if not modified_carriers.empty:
                    print(f"Updating {len(modified_carriers)} modified carrier records")

                    # Update modified records
                    for _, record in modified_carriers.iterrows():
                        target_conn.execute(
                            """
                            UPDATE carriers
                            SET list_status = ?, ns_day = ?,
                                route_s = ?, station = ?
                            WHERE effective_date = ? AND carrier_name = ?
                        """,
                            (
                                record["list_status"],
                                record["ns_day"],
                                record["route_s"],
                                record["station"],
                                record["effective_date"],
                                record["carrier_name"],
                            ),
                        )
                    stats["carriers_modified"] = len(modified_carriers)

                # If we added any records, update the sync log
                if (
                    stats["rings3_added"] > 0
                    or stats["carriers_added"] > 0
                    or stats["carriers_modified"] > 0
                ):
                    from datetime import datetime

                    now = datetime.now().isoformat()
                    target_conn.execute(
                        """
                        INSERT INTO sync_log (
                            sync_date,
                            rows_added_rings3,
                            rows_added_carriers
                        ) VALUES (?, ?, ?)
                    """,
                        (now, stats["rings3_added"], stats["carriers_added"]),
                    )

                    target_conn.commit()
                    print("Sync completed successfully!")
                    message = (
                        f"Sync completed successfully.\n"
                        f"Added {stats['rings3_added']} new clock rings\n"
                        f"Added {stats['carriers_added']} carrier records\n"
                        f"Modified {stats['carriers_modified']} existing carrier records"
                    )
                    CustomInfoDialog.information(self, "Sync Complete", message)

                    # Refresh both database status displays after successful sync
                    self.validate_database(self.mandates_db_path)
                    self.validate_eightbox_database()

                    return True, message, stats
                else:
                    target_conn.rollback()
                    print("No new records to add - databases are in sync")
                    CustomInfoDialog.information(
                        self, "Sync Complete", "No new records to sync"
                    )

                    # Still refresh status displays even if no changes were made
                    self.validate_database(self.mandates_db_path)
                    self.validate_eightbox_database()

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
                self, "Sync Error", f"An error occurred during sync:\n{str(e)}"
            )
            return False, f"Sync failed: {str(e)}", None
