"""Implementation of the Maximum 12-Hour Rule violation tracking tab.

This module provides specific implementation for tracking and displaying
violations of the 12-hour work limit, which prohibits carriers from working
more than 12 hours in a single day (11.50 hours for WAL carriers).
"""

import pandas as pd

from tabs.base import BaseViolationTab
from violation_model import ViolationModel
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

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in violation tab."""
        return date_data.copy()

    def add_summary_tab(self, data):
        """Create or update the summary tab with weekly violation totals.
        Shows total hours for daily columns but keeps Weekly Remedy Total.

        Args:
            data: DataFrame containing violation data
        """
        carrier_status = data.groupby("carrier_name")["list_status"].first()
        date_column = "rings_date" if "rings_date" in data.columns else "date"

        # Get daily totals using total_hours for the date columns
        daily_totals = data.pivot_table(
            index="carrier_name",
            columns=date_column,
            values="total_hours",
            aggfunc="sum",
            fill_value=0,
        )

        # Calculate weekly remedy total
        weekly_totals = data.groupby("carrier_name")["remedy_total"].sum()

        # Combine all data
        summary_data = pd.concat(
            [
                carrier_status.rename("list_status"),
                weekly_totals.rename("Weekly Remedy Total"),
                daily_totals,
            ],
            axis=1,
        ).reset_index()

        # Round numerical columns
        for col in summary_data.columns:
            if col not in ["carrier_name", "list_status"]:
                summary_data.loc[:, col] = summary_data[col].round(2)

        # Create model and view
        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = self.create_summary_proxy_model(model)
        view = self.create_table_view(model, proxy_model)

        self.summary_proxy_model = proxy_model
        self.date_tabs.addTab(view, "Summary")

        # Add violation count header
        violations = self._calculate_violation_count(summary_data)
        if "list_status" in summary_data.columns:
            ptf_violations = self._calculate_list_status_violation_count(
                summary_data, "ptf"
            )
            wal_violations = self._calculate_list_status_violation_count(
                summary_data, "wal"
            )
            nl_violations = self._calculate_list_status_violation_count(
                summary_data, "nl"
            )
            otdl_violations = self._calculate_list_status_violation_count(
                summary_data, "otdl"
            )

            header_text = (
                f"Total Violations: {violations}  |  "
                f"WAL: {wal_violations}  |  "
                f"NL: {nl_violations}  |  "
                f"OTDL: {otdl_violations}  |  "
                f"PTF: {ptf_violations}"
            )
            self.update_violation_header(
                self.date_tabs, self.date_tabs.count() - 1, violations, header_text
            )
        else:
            self.update_violation_header(
                self.date_tabs, self.date_tabs.count() - 1, violations
            )
