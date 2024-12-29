"""Database operations for carrier list management."""

import sqlite3

import pandas as pd

from custom_widgets import CustomNotificationDialog


class CarrierDBManager:
    """Manages database operations for carrier list functionality."""

    def __init__(self, mandates_db_path, eightbox_db_path):
        """Initialize the database manager.

        Args:
            mandates_db_path (str): Path to the mandates database
            eightbox_db_path (str): Path to the eightbox database
        """
        self.mandates_db_path = mandates_db_path
        self.eightbox_db_path = eightbox_db_path

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
            CustomNotificationDialog.show_notification(None, "Database Error", str(e))
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

    def create_ignored_carriers_table(self):
        """Create the ignored_carriers table if it doesn't exist."""
        with sqlite3.connect(self.eightbox_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ignored_carriers (
                    carrier_name TEXT PRIMARY KEY
                )
                """
            )
            conn.commit()

    def get_ignored_carriers(self):
        """Get list of ignored carriers.

        Returns:
            list: List of ignored carrier names
        """
        with sqlite3.connect(self.eightbox_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT carrier_name FROM ignored_carriers")
            return [row[0] for row in cursor.fetchall()]

    def add_to_ignored_carriers(self, carrier_names):
        """Add carriers to the ignored list.

        Args:
            carrier_names (list): List of carrier names to ignore
        """
        with sqlite3.connect(self.eightbox_db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO ignored_carriers (carrier_name) VALUES (?)",
                [(name,) for name in carrier_names],
            )
            conn.commit()
