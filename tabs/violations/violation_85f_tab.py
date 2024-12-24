"""Implementation of Article 8.5.F violation tracking tabs.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations, which occur when:
1. A non-OTDL carrier works more than 10 hours on a regularly scheduled day
2. A non-OTDL carrier works more than 8 hours on a non-scheduled day
3. A non-OTDL carrier works overtime on more than 4 of their 5 scheduled days
   in a service week

These rules do not apply during December (penalty overtime exclusion period).
"""

from tabs.base import BaseViolationTab
from violation_types import ViolationType


class Violation85fTab(BaseViolationTab):
    """Tab for displaying and managing Article 8.5.F violations.

    Tracks violations when non-OTDL carriers (WAL/NL) are required to work:
    - Over 10 hours on a regularly scheduled day
    - Over 8 hours on a non-scheduled day
    - Overtime on more than 4 of 5 scheduled days in a week

    The remedy calculation varies by violation type:
    - Regular day: Hours worked beyond 10 (if some were off-assignment)
    - Non-scheduled day: Hours worked beyond 8
    - 5th day: All overtime hours on the 5th overtime day

    Attributes:
        tab_type (ViolationType): Set to EIGHT_FIVE_F for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.EIGHT_FIVE_F

    def get_display_columns(self) -> list:
        """Return columns to display for 8.5.F violations.

        Returns:
            list: Column names specific to overtime violations
        """
        return [
            "carrier_name",
            "list_status",
            "date",
            "total_hours",
            "own_route_hours",
            "off_route_hours",
            "moves",
            "remedy_total",
            "violation_type",
        ]
