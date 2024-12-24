"""Database service module.

This module provides the main database service class for handling
database operations and data fetching.
"""

import json
import os
import sqlite3
from typing import Union, Tuple, Callable, Optional

import pandas as pd

from .models import ClockRingQueryParams, DatabaseError
from utils import set_display


class DatabaseService:
    """Handles all database operations and data fetching."""
    
    def __init__(self, error_handler: Optional[Callable] = None):
        """Initialize the database service.
        
        Args:
            error_handler: Optional callback for handling errors
                         (allows GUI-specific error handling)
        """
        self.error_handler = error_handler

    def fetch_clock_ring_data(
        self,
        params: ClockRingQueryParams
    ) -> Union[Tuple[pd.DataFrame, None], Tuple[None, DatabaseError]]:
        """Fetch clock ring data for the given parameters.
        
        This is a more functional approach that:
        1. Takes explicit parameters instead of using instance state
        2. Returns either (data, None) or (None, error)
        3. Separates data fetching from error display
        4. Makes testing easier
        
        Args:
            params: ClockRingQueryParams containing query parameters
            
        Returns:
            Tuple of (DataFrame, None) on success or (None, DatabaseError) on failure
        """
        try:
            # Validate database path
            if not self._validate_database_path(params.mandates_db_path):
                return None, DatabaseError(
                    message="No valid database path configured.\nPlease set a valid database path in Settings.",
                    error_type="PATH_ERROR"
                )

            # Execute the query
            data = self._execute_clock_ring_query(params)
            
            # Process carrier list
            data = self._process_carrier_list(data, params.carrier_list_path)
            
            # Add display indicators
            data = self._add_display_indicators(data)
            
            return data, None
            
        except Exception as e:
            error = DatabaseError(
                message=str(e),
                error_type="QUERY_ERROR",
                details={"exception": str(e)}
            )
            
            # Call error handler if provided
            if self.error_handler:
                self.error_handler(error)
                
            return None, error

    def _execute_clock_ring_query(
        self, params: ClockRingQueryParams
    ) -> pd.DataFrame:
        """Execute the main clock ring query.
        
        Args:
            params: Query parameters
            
        Returns:
            DataFrame containing the query results
            
        Raises:
            sqlite3.Error: If there's a database error
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
        WHERE r.rings_date >= DATE(?)
        AND r.rings_date < DATE(?, '+1 day')
        """

        with sqlite3.connect(params.mandates_db_path) as conn:
            db_data = pd.read_sql_query(
                query,
                conn,
                params=(
                    params.start_date.strftime("%Y-%m-%d"),
                    params.end_date.strftime("%Y-%m-%d")
                )
            )

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

            return db_data

    def _process_carrier_list(
        self, data: pd.DataFrame, carrier_list_path: str
    ) -> pd.DataFrame:
        """Process and merge carrier list data.
        
        Args:
            data: DataFrame with clock ring data
            carrier_list_path: Path to carrier list JSON
            
        Returns:
            DataFrame with carrier list data merged in
        """
        try:
            with open(carrier_list_path, "r") as json_file:
                carrier_list_df = pd.DataFrame(json.load(json_file))

            # Create a mapping of carrier names to their current list status
            carrier_status_map = carrier_list_df.set_index("carrier_name")[
                "list_status"
            ].to_dict()

            # Update list_status in data based on the JSON file
            data["list_status"] = (
                data["carrier_name"]
                .map(carrier_status_map)
                .fillna(data["list_status"])
            )

            # Get the full list of carriers from the JSON file
            carrier_names = carrier_list_df["carrier_name"].unique()

            # Create all date combinations
            all_dates = pd.date_range(
                start=data["rings_date"].min(),
                end=data["rings_date"].max(),
                inclusive="both"
            )

            all_combinations = pd.MultiIndex.from_product(
                [carrier_names, all_dates],
                names=["carrier_name", "rings_date"]
            )

            # Convert rings_date to datetime for proper comparison
            data["rings_date"] = pd.to_datetime(data["rings_date"])

            # Set index for reindexing
            data = data.set_index(["carrier_name", "rings_date"])

            # Reindex with all combinations
            data = data.reindex(all_combinations)

            # Fill missing values appropriately
            data = data.fillna(
                {
                    "total": 0,
                    "moves": "",
                    "code": "",
                    "leave_type": "",
                    "leave_time": "",
                    "list_status": data["list_status"].iloc[0]
                    if not data.empty
                    else "",
                }
            )

            # Reset index and convert dates back to string format
            data = data.reset_index()
            data["rings_date"] = data["rings_date"].dt.strftime("%Y-%m-%d")

            return data

        except FileNotFoundError:
            # If carrier_list.json doesn't exist, return original data
            return data

    def _add_display_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add display indicators to the data.
        
        Args:
            data: DataFrame to add indicators to
            
        Returns:
            DataFrame with display_indicator column added
        """
        data["display_indicator"] = data.apply(set_display, axis=1)
        return data

    def _validate_database_path(self, path: str) -> bool:
        """Validate the database path and required tables.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(path):
            return False

        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            required_tables = {"rings3", "carriers"}
            conn.close()

            return required_tables.issubset(tables)

        except Exception:
            return False 