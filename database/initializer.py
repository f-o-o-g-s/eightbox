"""Database initialization and management module.

This module handles the initialization and management of the Eightbox database,
including table creation, schema management, and data synchronization.
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd

from custom_widgets import CustomWarningDialog


class DatabaseInitializer:
    """Handles initialization and management of the Eightbox database.

    This class is responsible for:
    - Creating the database if it doesn't exist
    - Creating necessary tables and indexes
    - Synchronizing data from a source database
    - Managing database upgrades and migrations

    Attributes:
        target_path (str): Path where the database should be created/managed
        source_db_path (str, optional): Path to source database for data copying
        parent_widget: Parent widget for displaying dialogs (optional)
    """

    def __init__(self, target_path, source_db_path=None, parent_widget=None):
        """Initialize the DatabaseInitializer.

        Args:
            target_path (str): Path where the database should be created/managed
            source_db_path (str, optional): Path to source database for data copying
            parent_widget: Parent widget for displaying dialogs (optional)
        """
        self.target_path = target_path
        self.source_db_path = source_db_path
        self.parent_widget = parent_widget

    def initialize(self):
        """Initialize the database.

        Creates the database if it doesn't exist, or validates an existing one.
        Can optionally copy data from a source database during initialization.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If database exists and is valid, return True
            if os.path.exists(self.target_path):
                conn = sqlite3.connect(self.target_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in cursor.fetchall()}
                required_tables = {"rings3", "carriers", "sync_log"}
                if required_tables.issubset(tables):
                    conn.close()
                    # Perform sync if source_db_path is provided
                    if self.source_db_path and os.path.exists(self.source_db_path):
                        try:
                            # Connect to both databases
                            source_conn = sqlite3.connect(self.source_db_path)
                            target_conn = sqlite3.connect(self.target_path)

                            try:
                                # Start transaction
                                target_conn.execute("BEGIN TRANSACTION")
                                stats = {
                                    "rings3_added": 0,
                                    "carriers_added": 0,
                                    "carriers_modified": 0,
                                }

                                # Get new rings3 records
                                source_cursor = source_conn.cursor()
                                target_cursor = target_conn.cursor()

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

                                if new_records:
                                    target_conn.executemany(
                                        """
                                        INSERT INTO rings3 (
                                            rings_date, carrier_name, total, rs, code,
                                            moves, leave_type, leave_time, refusals,
                                            bt, et
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                        new_records,
                                    )
                                    stats["rings3_added"] = len(new_records)

                                # Handle carriers table
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

                                if new_carrier_records:
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
                                    now = datetime.now().isoformat()
                                    target_conn.execute(
                                        """
                                        INSERT INTO sync_log (
                                            sync_date,
                                            rows_added_rings3,
                                            rows_added_carriers
                                        ) VALUES (?, ?, ?)
                                    """,
                                        (
                                            now,
                                            stats["rings3_added"],
                                            stats["carriers_added"],
                                        ),
                                    )

                                    target_conn.commit()

                                    # Just log to console for debugging
                                    print(
                                        f"Initial sync completed successfully.\n"
                                        f"Added {stats['rings3_added']} new clock rings\n"
                                        f"Added {stats['carriers_added']} new carrier records\n"
                                        f"Updated {stats['carriers_modified']} carrier records"
                                    )
                                else:
                                    target_conn.rollback()
                                    print("No new records to sync")

                            finally:
                                source_conn.close()
                                target_conn.close()

                        except Exception as e:
                            print(f"Error during initial sync: {str(e)}")
                            if self.parent_widget:
                                CustomWarningDialog.warning(
                                    self.parent_widget,
                                    "Sync Error",
                                    f"An error occurred during initial sync:\n{str(e)}",
                                )
                    return True

            # Create new database
            conn = sqlite3.connect(self.target_path)
            cursor = conn.cursor()

            # Create tables
            self._create_tables(cursor)

            # Create recommended indexes
            self._create_indexes(cursor)

            # If source database provided, copy data
            if self.source_db_path and os.path.exists(self.source_db_path):
                cursor.execute("ATTACH DATABASE ? AS source", (self.source_db_path,))

                # Copy data in a transaction
                cursor.execute("BEGIN TRANSACTION")
                try:
                    cursor.execute("INSERT INTO carriers SELECT * FROM source.carriers")
                    cursor.execute("INSERT INTO rings3 SELECT * FROM source.rings3")
                    cursor.execute("COMMIT")
                except Exception:
                    cursor.execute("ROLLBACK")
                    raise
                finally:
                    cursor.execute("DETACH DATABASE source")

                # Add initial sync log entry
                now = datetime.now().isoformat()
                cursor.execute(
                    """
                    INSERT INTO sync_log (
                        sync_date,
                        rows_added_rings3,
                        rows_added_carriers,
                        backup_path
                    ) VALUES (?, 0, 0, NULL)
                """,
                    (now,),
                )

                return True

        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    def _create_tables(self, cursor):
        """Create the required database tables.

        Args:
            cursor: SQLite cursor object
        """
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

    def _create_indexes(self, cursor):
        """Create the recommended database indexes.

        Args:
            cursor: SQLite cursor object
        """
        cursor.execute("CREATE INDEX idx_rings3_date ON rings3(rings_date)")
        cursor.execute("CREATE INDEX idx_carrier_name ON carriers(carrier_name)")
        cursor.execute(
            "CREATE INDEX idx_rings3_carrier_date ON rings3(carrier_name, rings_date)"
        )
