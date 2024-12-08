"""Implementation of Article 8.5.F non-scheduled day violation tracking tab.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations that occur when non-OTDL carriers work more than
8 hours on their non-scheduled days.
"""

import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
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

    def create_tab_for_date(self, date, date_data):
        """Create a tab for the given date.
        
        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            Filters the data to show only relevant columns for non-scheduled
            day violations, including carrier name, list status, total hours,
            and remedy hours.
        """
        # Filter to display columns
        display_columns = [
            "carrier_name",
            "list_status",
            "violation_type",
            "date",
            "remedy_total",
            "total_hours",
        ]
        filtered_data = date_data[display_columns]

        model = ViolationModel(filtered_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view
