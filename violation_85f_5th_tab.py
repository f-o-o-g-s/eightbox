"""Implementation of Article 8.5.F fifth overtime day violation tracking tab.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations that occur when non-OTDL carriers work overtime
on more than 4 of their 5 scheduled days in a service week.
"""

import pandas as pd
from PyQt5.QtWidgets import QTableView

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
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.EIGHT_FIVE_F_5TH

    def get_display_columns(self) -> list:
        """Return columns to display for 5th overtime day violations.
        
        Returns:
            list: Column names specific to 5th overtime day violations
        """
        return [
            "carrier_name",
            "list_status",
            "date",
            "daily_hours",
            "total_hours",
            "remedy_total",
            "violation_type",
        ]

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in 5th overtime day violation tab.
        
        Adds special formatting for daily hours with overtime indicators.
        
        Args:
            date_data: Raw violation data for a specific date
            
        Returns:
            Formatted data with combined daily hours and indicators
        """
        # Create a copy to avoid modifying original
        formatted_data = date_data.copy()

        # Add display indicator if not present
        if "display_indicator" not in formatted_data.columns:
            formatted_data["display_indicator"] = formatted_data.apply(set_display, axis=1)

        # Format daily hours with indicator
        formatted_data["daily_hours"] = formatted_data.apply(
            lambda row: (
                f"{row['total_hours']:.2f} {row['display_indicator']}"
                if pd.notna(row["total_hours"])
                else row["display_indicator"]
            ),
            axis=1,
        )

        return formatted_data

    def configure_tab_view(self, view: QTableView, model: ViolationModel):
        """Configure the tab view after creation.
        
        Hides the violation_dates column which is only used internally.
        
        Args:
            view: The table view to configure
            model: The model containing the data
        """
        # Hide violation_dates column
        if "violation_dates" in model.df.columns:
            column_idx = model.df.columns.get_loc("violation_dates")
            view.setColumnHidden(column_idx, True)
