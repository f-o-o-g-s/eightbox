"""Implementation of the Maximum 60-Hour Rule violation tracking tab.

This module provides specific implementation for tracking and displaying
violations of the 60-hour work limit, which prohibits carriers from
accumulating more than 60 work hours in a service week.
"""
import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_types import ViolationType


class ViolationMax60Tab(BaseViolationTab):
    """Tab for displaying and managing Maximum 60-Hour Rule violations.

    Tracks weekly hour accumulation including:
    - Regular work hours
    - Overtime hours
    - All types of paid leave
    - Holiday pay

    The remedy is calculated as total weekly hours minus 60.

    Attributes:
        tab_type (ViolationType): Set to MAX_60 for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.MAX_60

    def get_display_columns(self) -> list:
        """Return columns to display for 60-hour violations.

        Returns:
            list: Column names specific to 60-hour limit violations
        """
        return [
            "carrier_name",
            "list_status",
            "date",
            "daily_hours",
            "cumulative_hours",
            "remedy_total",
            "violation_type",
        ]

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in 60-hour violation tab.

        Adds special formatting for daily hours with leave type indicators.

        Args:
            date_data: Raw violation data for a specific date

        Returns:
            Formatted data with combined daily hours and indicators
        """
        # Create a copy to avoid modifying original
        formatted_data = date_data.copy()

        # Format daily hours with display indicator
        formatted_data["daily_hours"] = formatted_data.apply(
            lambda row: (
                f"{row['daily_hours']:.2f} {row['display_indicator']}"
                if pd.notna(row["daily_hours"])
                else row["display_indicator"]
            ),
            axis=1,
        )

        return formatted_data
