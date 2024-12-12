"""Implementation of the violations summary tab.

This module provides a summary view of all violations across different types,
allowing for quick analysis and comparison of violation patterns.
"""
import pandas as pd

from base_violation_tab import BaseViolationTab
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

    # Define standard order of violation types
    VIOLATION_ORDER = [
        "8.5.D",
        "8.5.F",
        "8.5.F NS",
        "8.5.F 5th",
        "MAX12",
        "MAX60",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = ViolationType.VIOLATION_REMEDIES

    def get_display_columns(self) -> list:
        """Return columns to display for violation summary.

        Returns:
            list: Standard column order for summary view
        """
        return ["carrier_name", "list_status"] + self.VIOLATION_ORDER + ["Remedy Total"]

    def format_display_data(self, date_data: pd.DataFrame) -> pd.DataFrame:
        """Format data for display in summary tab.

        Adds combined remedy total and ensures consistent column ordering.

        Args:
            date_data: Raw violation data for a specific date

        Returns:
            Formatted data with remedy totals and ordered columns
        """
        # Create a copy to avoid modifying original
        formatted_data = date_data.copy()

        # Add Remedy Total if not present
        if "Remedy Total" not in formatted_data.columns:
            formatted_data["Remedy Total"] = (
                formatted_data.select_dtypes(include=["number"]).sum(axis=1).round(2)
            )

        # Reorder columns based on which violation types are present
        existing_violations = [
            col for col in self.VIOLATION_ORDER if col in formatted_data.columns
        ]
        ordered_columns = (
            ["carrier_name", "list_status"] + existing_violations + ["Remedy Total"]
        )
        formatted_data = formatted_data[ordered_columns]

        return formatted_data

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

        # Clear existing tabs
        while self.date_tabs.count():
            self.date_tabs.removeTab(0)
        self.models.clear()
        self.showing_no_data = False

        # Reorder columns based on desired order
        new_columns = []
        for date in sorted(data.columns.get_level_values(0).unique()):
            if date in ["carrier_name", "list_status"]:
                new_columns.append((date, ""))
            else:
                for violation_type in self.VIOLATION_ORDER:
                    if (date, violation_type) in data.columns:
                        new_columns.append((date, violation_type))

        data = data[new_columns]

        # Create tabs for each date
        unique_dates = sorted(
            date
            for date in data.columns.get_level_values(0).unique()
            if date not in ["carrier_name", "list_status"]
        )

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
        self.restore_tab_selection(current_tab_name)

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

            # Filter and order violation types
            summary_data = summary_data[
                [col for col in self.VIOLATION_ORDER if col in summary_data.columns]
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
            model, view = self.create_summary_model(summary_data)

            # Calculate total violations for each list status
            total_violations = 0
            wal_violations = 0
            nl_violations = 0
            otdl_violations = 0
            ptf_violations = 0

            # Count carriers with violations by list status
            carriers_with_violations = summary_data[
                summary_data["Weekly Remedy Total"] > 0
            ]
            list_status_violations = (
                carriers_with_violations["list_status"].str.lower().value_counts()
            )

            # Get counts for each list status
            wal_violations = list_status_violations.get("wal", 0)
            nl_violations = list_status_violations.get("nl", 0)
            otdl_violations = list_status_violations.get("otdl", 0)
            ptf_violations = list_status_violations.get("ptf", 0)
            total_violations = sum(
                [wal_violations, nl_violations, otdl_violations, ptf_violations]
            )

            # Count total carriers by list status
            total_carriers = len(summary_data)
            list_status_counts = summary_data["list_status"].str.lower().value_counts()
            wal_carriers = list_status_counts.get("wal", 0)
            nl_carriers = list_status_counts.get("nl", 0)
            otdl_carriers = list_status_counts.get("otdl", 0)
            ptf_carriers = list_status_counts.get("ptf", 0)

            # Create the header text
            total_carriers_text = (
                f"Total Carriers: {total_carriers} | "
                f"WAL: {wal_carriers} | "
                f"NL: {nl_carriers} | "
                f"OTDL: {otdl_carriers} | "
                f"PTF: {ptf_carriers}"
            )

            carriers_violations_text = (
                f"Carriers With Violations: {total_violations} | "
                f"WAL: {wal_violations} | "
                f"NL: {nl_violations} | "
                f"OTDL: {otdl_violations} | "
                f"PTF: {ptf_violations}"
            )

            # Add the tab
            tab_index = self.date_tabs.addTab(view, "Summary")

            # Update the header with both rows
            self.update_violation_header(
                self.date_tabs,
                tab_index,
                total_violations,
                f"{total_carriers_text}\n{carriers_violations_text}",
            )

        except Exception as e:
            print(f"Error during summary aggregation: {e}")
