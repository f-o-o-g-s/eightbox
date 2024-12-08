"""Implementation of the Maximum 12-Hour Rule violation tracking tab.

This module provides specific implementation for tracking and displaying
violations of the 12-hour work limit, which prohibits carriers from working
more than 12 hours in a single day (11.50 hours for WAL carriers).
"""

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
from violation_types import ViolationType


class ViolationMax12Tab(BaseViolationTab):
    """Tab for displaying and managing Maximum 12-Hour Rule violations.

    Tracks violations when carriers exceed their daily hour limit:
    - OTDL carriers: 12.00 hours
    - WAL carriers: 11.50 hours
    - NL carriers: 12.00 hours

    The remedy is calculated as the total hours worked minus the applicable limit.

    Attributes:
        tab_type (ViolationType): Set to MAX_12 for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.MAX_12

    def get_display_columns(self) -> list:
        """Return columns to display for 12-hour violations.
        
        Returns:
            list: Column names specific to daily hour limit violations
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
