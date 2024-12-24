"""Database service for handling clock ring data operations."""

import sqlite3
from typing import Tuple

import pandas as pd

from .models import (
    ClockRingQueryParams,
    DatabaseError,
)


class DatabaseService:
    """Service class for database operations."""

    def fetch_clock_ring_data(
        self, params: ClockRingQueryParams
    ) -> Tuple[pd.DataFrame, DatabaseError]:
        """Fetch clock ring data from the database.

        Args:
            params: Query parameters including dates and database path

        Returns:
            Tuple containing:
            - DataFrame with clock ring data
            - DatabaseError if any occurred, None otherwise
        """
        try:
            # Validate database path
            if not params.mandates_db_path:
                return pd.DataFrame(), DatabaseError(
                    "No database path configured",
                    "Please configure the database path in Settings.",
                )

            # Connect to database
            conn = sqlite3.connect(params.mandates_db_path)

            # Build query with date range
            query = """
                SELECT
                    carrier_name,
                    rings_date,
                    total,
                    moves,
                    code,
                    leave_type,
                    leave_time,
                    display_indicator
                FROM mandates
                WHERE rings_date >= DATE(?)
                AND rings_date < DATE(?, '+1 day')
                ORDER BY carrier_name, rings_date
            """

            # Execute query and load into DataFrame
            df = pd.read_sql_query(
                query,
                conn,
                params=(
                    params.start_date.strftime("%Y-%m-%d"),
                    params.end_date.strftime("%Y-%m-%d"),
                ),
                parse_dates=["rings_date"],
            )

            conn.close()
            return df, None

        except sqlite3.Error as e:
            error_msg = (
                "Failed to fetch data from database. "
                "Please check your database configuration."
            )
            return pd.DataFrame(), DatabaseError(error_msg, str(e))

        except Exception as e:
            return pd.DataFrame(), DatabaseError("An unexpected error occurred", str(e))
