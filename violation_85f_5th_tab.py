"""Implementation of Article 8.5.F fifth overtime day violation tracking tab.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations that occur when non-OTDL carriers work overtime
on more than 4 of their 5 scheduled days in a service week.
"""

import pandas as pd

from base_violation_tab import BaseViolationTab
from utils import set_display
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
from violation_types import ViolationType


class Violation85f5thTab(BaseViolationTab):
    """Tab for displaying and managing Article 8.5.F fifth overtime day violations.

    Handles violations related to working overtime on more than 4 of 5
    scheduled days in a service week. Provides specialized tracking and
    display features including:
    - Daily violation details with indicators
    - Fifth overtime occurrence dates
    - Weekly remedy totals per carrier
    - List status filtering
    - Remedy hour calculations
    - Service week boundaries

    Attributes:
        tab_type (ViolationType): Set to EIGHT_FIVE_F_5TH for this violation type
        showing_no_data (bool): Indicates if the "No Data" placeholder is shown
        models (dict): Collection of models and views for each date tab
        date_tabs (QTabWidget): Widget containing all date-specific tabs
        summary_proxy_model (ViolationFilterProxyModel): Model for summary tab
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.EIGHT_FIVE_F_5TH

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing violations for a specific date.

        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            Adds special display indicators for fifth overtime day occurrences
            and hides the violation_dates column which is only used internally.
        """
        # Create a copy of the data to avoid SettingWithCopyWarning
        date_data = date_data.copy()

        # Add display indicator and combine with total_hours
        if "display_indicator" not in date_data.columns:
            date_data["display_indicator"] = date_data.apply(set_display, axis=1)

        date_data["daily_hours"] = date_data.apply(
            lambda row: (
                f"{row['total_hours']:.2f} {row['display_indicator']}"
                if pd.notna(row["total_hours"])
                else row["display_indicator"]
            ),
            axis=1,
        )

        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        # Hide violation_dates column
        if "violation_dates" in model.df.columns:
            column_idx = model.df.columns.get_loc("violation_dates")
            view.setColumnHidden(column_idx, True)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view
