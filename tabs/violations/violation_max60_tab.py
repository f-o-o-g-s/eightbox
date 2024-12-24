"""Implementation of the Maximum 60-Hour Rule violation tracking tab.

This module provides specific implementation for tracking and displaying
violations of the 60-hour work limit, which prohibits carriers from
accumulating more than 60 work hours in a service week.
"""
import pandas as pd

from tabs.base import BaseViolationTab
from violation_model import ViolationModel
from violation_types import ViolationType


class ViolationMax60Tab(BaseViolationTab):
    """Tab for displaying and managing Maximum 60-Hour Rule violations.

    Tracks weekly hour accumulation including:
    - Regular work hours
    - Overtime hours
    - All types of paid leave
    - Holiday pay

    The remedy is calculated as total weekly hours minus 60.

    Attributes:
        tab_type (ViolationType): Set to MAX_60 for this violation type
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.MAX_60

    def get_display_columns(self) -> list:
        """Return columns to display for 60-hour violations.

        Returns:
            list: Column names specific to 60-hour limit violations
        """
        return [
            "carrier_name",
            "list_status",
            "date",
            "daily_hours",
            "cumulative_hours",
            "remedy_total",
            "violation_type",
        ]

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in 60-hour violation tab.

        Adds special formatting for daily hours with leave type indicators.

        Args:
            date_data: Raw violation data for a specific date

        Returns:
            Formatted data with combined daily hours and indicators
        """
        # Create a copy to avoid modifying original
        formatted_data = date_data.copy()

        # Format daily hours with display indicator
        formatted_data["daily_hours"] = formatted_data.apply(
            lambda row: (
                f"{row['daily_hours']:.2f} {row['display_indicator']}"
                if pd.notna(row["daily_hours"])
                else row["display_indicator"]
            ),
            axis=1,
        )

        return formatted_data

    def add_summary_tab(self, data):
        """Create or update the summary tab with weekly violation totals.
        Shows daily hours for each date, plus Total Weekly Hours and Weekly Remedy Total.

        Args:
            data: DataFrame containing violation data
        """
        carrier_status = data.groupby("carrier_name")["list_status"].first()
        date_column = "rings_date" if "rings_date" in data.columns else "date"

        # Get daily totals using daily_hours for the date columns
        daily_totals = data.pivot_table(
            index="carrier_name",
            columns=date_column,
            values="daily_hours",
            aggfunc="sum",
            fill_value=0,
        )

        # Get final cumulative hours for each carrier
        final_cumulative = data.groupby("carrier_name")["cumulative_hours"].max()

        # Calculate weekly remedy total
        weekly_totals = data.groupby("carrier_name")["remedy_total"].sum()

        # Combine all data
        summary_data = pd.concat(
            [
                carrier_status.rename("list_status"),
                weekly_totals.rename("Weekly Remedy Total"),
                final_cumulative.rename("Total Weekly Hours"),
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
