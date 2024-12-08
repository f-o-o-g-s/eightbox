"""Implementation of Article 8.5.F non-scheduled day violation tracking tab.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations that occur when non-OTDL carriers work more than
8 hours on their non-scheduled days.
"""

from base_violation_tab import BaseViolationTab
from violation_types import ViolationType


class Violation85fNsTab(BaseViolationTab):
    """Tab for displaying and managing Article 8.5.F non-scheduled day violations.

    Handles violations related to overtime work on non-scheduled days.
    Provides daily and summary views of violations, including:
    - Daily violation details
    - Weekly totals per carrier
    - List status filtering
    - Remedy hour calculations

    Attributes:
        tab_type (ViolationType): Set to EIGHT_FIVE_F_NS for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.EIGHT_FIVE_F_NS

    def get_display_columns(self) -> list:
        """Return columns to display for non-scheduled day violations.

        Returns:
            list: Column names specific to non-scheduled day violations
        """
        return [
            "carrier_name",
            "list_status",
            "violation_type",
            "date",
            "remedy_total",
            "total_hours",
        ]
