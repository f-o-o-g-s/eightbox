"""Implementation of the Article 8.5.D violation tracking tab.

This module provides the specific implementation for tracking and displaying
Article 8.5.D violations, which occur when carriers work off their bid assignments
without proper notification.
"""

import pandas as pd

from base_violation_tab import BaseViolationTab
from utils import set_display
from violation_types import ViolationType


class Violation85dTab(BaseViolationTab):
    """Tab for displaying and managing Article 8.5.D violations.

    Handles violations related to carriers working off their bid assignments.
    Provides daily and summary views of violations, including:
    - Daily violation details
    - Weekly totals per carrier
    - List status filtering
    - Remedy hour calculations

    Attributes:
        tab_type (ViolationType): Set to EIGHT_FIVE_D for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.EIGHT_FIVE_D

    def get_display_columns(self) -> list:
        """Return columns to display for 8.5.D violations.

        Returns:
            list: Column names specific to off-assignment violations
        """
        return [
            "carrier_name",
            "list_status",
            "date",
            "total_hours",
            "own_route_hours",
            "off_route_hours",
            "moves",
            "display_indicator",
            "remedy_total",
            "violation_type",
        ]

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in 8.5.D violation tab.

        Adds special formatting for daily hours with status indicators.

        Args:
            date_data: Raw violation data for a specific date

        Returns:
            Formatted data with combined daily hours and indicators
        """
        # Create a copy to avoid modifying original
        formatted_data = date_data.copy()

        # Add display indicator if not present
        if "display_indicator" not in formatted_data.columns:
            formatted_data["display_indicator"] = formatted_data.apply(
                set_display, axis=1
            )

        # Format total hours with indicator
        formatted_data["total_hours"] = formatted_data.apply(
            lambda row: (
                f"{row['total_hours']:.2f} {row['display_indicator']}"
                if pd.notna(row["total_hours"])
                else row["display_indicator"]
            ),
            axis=1,
        )

        return formatted_data
