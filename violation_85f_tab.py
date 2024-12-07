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

    def add_summary_tab(self, data):
        """Create or update the summary tab with weekly violation totals.

        Aggregates violation data to show:
        - Carrier list status
        - Weekly remedy total from all 8.5.F violations
        - Daily violation totals
        - All values rounded to 2 decimal places

        Args:
            data (pd.DataFrame): Complete violation data for the week

        Note:
            Handles both regular day and non-scheduled day violations,
            combining remedies when multiple violation types occur.
        """
        # Get carrier statuses and daily totals
        carrier_status = data.groupby("carrier_name")["list_status"].first()

        # Get daily totals using the correct column names
        value_column = "total" if "total" in data.columns else "remedy_total"
        date_column = "rings_date" if "rings_date" in data.columns else "date"

        daily_totals = data.pivot_table(
            index="carrier_name",
            columns=date_column,
            values=value_column,
            aggfunc="sum",
            fill_value=0,
        )

        # Calculate weekly totals
        weekly_totals = data.groupby("carrier_name")[value_column].sum()

        # Combine everything
        summary_data = pd.concat(
            [
                carrier_status.rename("list_status"),
                weekly_totals.rename("Weekly Remedy Total"),
                daily_totals,
            ],
            axis=1,
        )

        # Reset index to make carrier_name a column
        summary_data = summary_data.reset_index()

        # Reorder columns to put list_status after carrier_name
        columns = summary_data.columns.tolist()
        columns.remove("list_status")
        columns.insert(1, "list_status")
        summary_data = summary_data[columns]

        # Round numerical columns
        for col in summary_data.columns:
            if col not in ["carrier_name", "list_status"]:
                summary_data[col] = summary_data[col].round(2)

        # Create model and view
        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.summary_proxy_model = proxy_model
        self.date_tabs.addTab(view, "Summary")

    def refresh_data(self, violation_data):
        """Refresh all tabs with new violation data.

        Clears existing tabs and creates new ones based on the provided data.
        Maintains the currently selected tab when possible.

        Args:
            violation_data (pd.DataFrame): New violation data containing:
                - carrier_name: Name of the carrier
                - list_status: WAL/NL/OTDL status
                - date: Date of potential violation
                - total_hours: Total hours worked that day
                - off_route_hours: Hours worked off assignment
                - remedy_total: Calculated remedy hours

        Note:
            - Creates a tab for each date in the data
            - Adds a summary tab showing weekly totals
            - Shows "No Data" tab if violation_data is empty
            - Excludes OTDL carriers and December dates
            - Handles both regular day and non-scheduled day violations
            - Tracks 5th day of overtime violations within service weeks
        """
        if violation_data.empty:
            self.init_no_data_tab()
            return

        current_tab_index = self.date_tabs.currentIndex()
        current_tab_name = self.date_tabs.tabText(current_tab_index)

        while self.date_tabs.count():
            self.date_tabs.removeTab(0)
        self.models.clear()
        self.showing_no_data = False

        date_column = "rings_date" if "rings_date" in violation_data.columns else "date"

        # Create tabs for each date
        for date in sorted(violation_data[date_column].unique()):
            date_data = violation_data[violation_data[date_column] == date]
            self.create_tab_for_date(date, date_data)

        # Add summary tab
        self.add_summary_tab(violation_data)

        # Restore tab selection
        if current_tab_name == "Summary":
            self.date_tabs.setCurrentIndex(self.date_tabs.count() - 1)
        else:
            for i in range(self.date_tabs.count()):
                if self.date_tabs.tabText(i) == current_tab_name:
                    self.date_tabs.setCurrentIndex(i)
                    break
