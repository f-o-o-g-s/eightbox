"""Implementation of Article 8.5.F violation tracking tabs.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations, which occur when:
1. A non-OTDL carrier works more than 10 hours on a regularly scheduled day
2. A non-OTDL carrier works more than 8 hours on a non-scheduled day
3. A non-OTDL carrier works overtime on more than 4 of their 5 scheduled days
   in a service week

These rules do not apply during December (penalty overtime exclusion period).
"""

import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
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

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing violations for a specific date.

        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            Displays carrier name, list status, total hours worked,
            and remedy hours based on the specific type of 8.5.F
            violation that occurred.
        """
        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view
