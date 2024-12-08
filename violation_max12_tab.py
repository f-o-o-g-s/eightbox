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

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing violations for a specific date.

        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            Displays carrier name, list status, total hours worked,
            and remedy hours (hours beyond 12.00 or 11.50).
        """
        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view
