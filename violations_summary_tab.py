"""Implementation of the Violations Summary tab.

This module provides a specialized implementation for displaying an aggregated
view of all violation types in a single interface. It combines data from:
- Article 8.5.D violations (off-assignment work)
- Article 8.5.F violations (overtime limits)
- Maximum 12-Hour Rule violations
- Maximum 60-Hour Rule violations

The summary provides both daily breakdowns and weekly totals for each
violation type, allowing for easy tracking of multiple violation categories.
"""

import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
from violation_types import ViolationType


class ViolationRemediesTab(BaseViolationTab):
    """Tab for displaying aggregated violation data across all violation types.

    Provides a comprehensive view of all violation categories including:
    - Daily violation breakdowns by type
    - Weekly totals per violation type
    - Combined remedy totals
    - List status filtering
    - Carrier-specific violation history

    The display is organized to show:
    - 8.5.D violations (off-assignment work)
    - 8.5.F violations (regular day overtime)
    - 8.5.F NS violations (non-scheduled day)
    - 8.5.F 5th day violations
    - MAX12 violations (12-hour limit)
    - MAX60 violations (weekly limit)

    Attributes:
        tab_type (ViolationType): Set to VIOLATION_REMEDIES for this summary view
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.VIOLATION_REMEDIES

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing all violation types for a specific date.

        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Combined violation data for the date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            Organizes violations in a standard order and calculates
            combined remedy totals for each carrier.
        """
        # Prepare data for each date tab
        date_data = date_data.copy()

        # Add Remedy Total (daily version)
        if "Remedy Total" not in date_data.columns:
            date_data["Remedy Total"] = (
                date_data.select_dtypes(include=["number"]).sum(axis=1).round(2)
            )

        # Define the desired order of violation types
        desired_order = ["8.5.D", "8.5.F", "8.5.F NS", "8.5.F 5th", "MAX12", "MAX60"]

        # Reorder columns if they exist
        existing_violations = [col for col in desired_order if col in date_data.columns]
        ordered_columns = (
            ["carrier_name", "list_status"] + existing_violations + ["Remedy Total"]
        )
        date_data = date_data[ordered_columns]

        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view

    def refresh_data(self, data):
        """Refresh the tabs with aggregated violation data.

        This implementation differs from the base class to handle the
        multi-indexed DataFrame that contains all violation types.

        Args:
            data (pd.DataFrame): Multi-indexed DataFrame containing all violation data

        Note:
            Expects a DataFrame with a MultiIndex column structure where:
            - Level 0 contains dates and carrier info
            - Level 1 contains violation types
        """
        if data.empty or not isinstance(data.columns, pd.MultiIndex):
            self.init_no_data_tab()
            return

        current_tab_index = self.date_tabs.currentIndex()
        current_tab_name = self.date_tabs.tabText(current_tab_index)

        while self.date_tabs.count():
            self.date_tabs.removeTab(0)
        self.models.clear()
        self.showing_no_data = False

        # Define the desired order of violation types
        desired_order = ["8.5.D", "8.5.F", "8.5.F NS", "8.5.F 5th", "MAX12", "MAX60"]

        # Reorder columns based on desired order
        new_columns = []
        for date in sorted(data.columns.get_level_values(0).unique()):
            if date in ["carrier_name", "list_status"]:
                new_columns.append((date, ""))
            else:
                for violation_type in desired_order:
                    if (date, violation_type) in data.columns:
                        new_columns.append((date, violation_type))

        data = data[new_columns]

        # Group data by date
        unique_dates = sorted(
            date
            for date in data.columns.get_level_values(0).unique()
            if date not in ["carrier_name", "list_status"]
        )

        # Create tabs for each date
        for date in unique_dates:
            date_data = data.xs(date, level=0, axis=1).copy()
            if "carrier_name" in data.columns.get_level_values(0):
                date_data.insert(0, "carrier_name", data["carrier_name"])
            if "list_status" in data.columns.get_level_values(0):
                date_data.insert(1, "list_status", data["list_status"])

            self.create_tab_for_date(date, date_data)

        # Add summary tab
        self.add_summary_tab(data)

        # Restore tab selection
        if current_tab_name == "Summary":
            self.date_tabs.setCurrentIndex(self.date_tabs.count() - 1)
        else:
            for i in range(self.date_tabs.count()):
                if self.date_tabs.tabText(i) == current_tab_name:
                    self.date_tabs.setCurrentIndex(i)
                    break

    def add_summary_tab(self, data):
        """Create a summary tab showing weekly totals for all violation types.

        Args:
            data (pd.DataFrame): Multi-indexed DataFrame with all violation data

        Note:
            Creates a summary that shows:
            - Weekly total for each violation type
            - Combined weekly remedy total
            - Carrier list status
            All numerical values are rounded to 2 decimal places.
        """
        try:
            # Aggregate data for summary
            summary_data = (
                data.select_dtypes(include=["number"]).T.groupby(level=1).sum().T
            )

            # Define the desired order of violation types
            desired_order = [
                "8.5.D",
                "8.5.F",
                "8.5.F NS",
                "8.5.F 5th",
                "MAX12",
                "MAX60",
            ]
            summary_data = summary_data[
                [col for col in desired_order if col in summary_data.columns]
            ]

            # Add Weekly Remedy Total
            summary_data["Weekly Remedy Total"] = summary_data.sum(axis=1).round(2)
            summary_data = summary_data.round(2)

            # Include carrier_name and list_status
            if "carrier_name" in data.columns.get_level_values(0):
                summary_data.insert(0, "carrier_name", data["carrier_name"])
            if "list_status" in data.columns.get_level_values(0):
                summary_data.insert(1, "list_status", data["list_status"])

            summary_data.reset_index(drop=True, inplace=True)

            # Create model and view
            model = ViolationModel(
                summary_data, tab_type=self.tab_type, is_summary=True
            )
            proxy_model = ViolationFilterProxyModel()
            proxy_model.setSourceModel(model)
            view = self.create_table_view(model, proxy_model)

            self.summary_proxy_model = proxy_model
            self.date_tabs.addTab(view, "Summary")

        except Exception as e:
            print(f"Error during summary aggregation: {e}")
