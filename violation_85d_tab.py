"""Implementation of the Article 8.5.D violation tracking tab.

This module provides the specific implementation for tracking and displaying
Article 8.5.D violations, which occur when carriers work off their bid assignments
without proper notification.
"""

import pandas as pd

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

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing violations for a specific date.

        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            The model is configured specifically for 8.5.D violations,
            showing relevant columns like carrier name, list status,
            and remedy hours.
        """
        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view
