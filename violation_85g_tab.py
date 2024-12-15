"""Implementation of the Article 8.5.G violation tracking tab.

This module provides the specific implementation for tracking and displaying
Article 8.5.G violations, which occur when OTDL carriers are not maximized
while WAL/NL carriers work overtime off assignment.
"""

from base_violation_tab import BaseViolationTab
from violation_types import ViolationType


class Violation85gTab(BaseViolationTab):
    """Tab for displaying and managing Article 8.5.G violations.

    Handles violations related to OTDL carriers not being maximized. Shows both:
    - OTDL carriers who should have received more hours (with remedies)
    - WAL/NL carriers whose overtime work triggered the violations

    Provides daily and summary views of violations, including:
    - Daily violation details with hour limits
    - Weekly totals per carrier
    - List status filtering
    - Remedy hour calculations
    - Trigger carrier information

    Attributes:
        tab_type (ViolationType): Set to EIGHT_FIVE_G for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.EIGHT_FIVE_G

    def get_display_columns(self) -> list:
        """Return columns to display for 8.5.G violations.

        Returns:
            list: Column names specific to OTDL maximization violations,
                 including trigger carrier information
        """
        return [
            "carrier_name",
            "list_status",
            "date",
            "hour_limit",
            "total_hours",
            "remedy_total",
            "display_indicators",  # Changed from display_indicator
            "violation_type",  # Shows "8.5.G OTDL Not Maximized" or "8.5.G Trigger (No Remedy)"
            "trigger_carrier",  # WAL/NL carrier that triggered the violation
            "trigger_hours",  # Hours worked by trigger carrier
            "off_route_hours",  # Off-route hours that triggered violation
        ]

    def format_data(self, data):
        """Format the violation data for display.

        Ensures consistent numerical formatting and handles special cases.
        Hides trigger information for non-violation entries.

        Args:
            data: DataFrame containing violation data

        Returns:
            DataFrame: Formatted violation data ready for display
        """
        formatted = super().format_data(data)

        # Ensure consistent decimal places for numerical columns
        numeric_columns = [
            "hour_limit",
            "total_hours",
            "remedy_total",
            "trigger_hours",
            "off_route_hours",
        ]
        for col in numeric_columns:
            if col in formatted.columns:
                formatted[col] = formatted[col].round(2)

        # Update violation type display
        if "violation_type" in formatted.columns:
            # Convert simple "8.5.G" to display version
            formatted.loc[
                formatted["violation_type"] == "8.5.G", "violation_type"
            ] = "8.5.G OTDL Not Maximized"

            # Hide trigger info and display indicator for non-violations
            no_violation_mask = formatted["remedy_total"] == 0
            for col in ["trigger_carrier", "trigger_hours", "off_route_hours", "display_indicator"]:
                if col in formatted.columns:
                    formatted.loc[no_violation_mask, col] = ""

        return formatted
