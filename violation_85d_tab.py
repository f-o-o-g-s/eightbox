"""Implementation of the Article 8.5.D violation tracking tab.

This module provides the specific implementation for tracking and displaying
Article 8.5.D violations, which occur when carriers work off their bid assignments
without proper notification.
"""

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
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
            "remedy_total",
        ]
