"""Implementation of the violations summary tab.

This module provides a summary view of all violations across different types,
allowing for quick analysis and comparison of violation patterns.
"""
import traceback

import pandas as pd

from tabs.base import BaseViolationTab
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
    - 8.5.G violations (OTDL not maximized)
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
        "8.5.G",
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

    def refresh_data(self, violation_data):
        """Refresh the tabs with aggregated violation data.

        Args:
            violation_data (pd.DataFrame): DataFrame containing all violation data with columns like
                               'date_violation_type' containing remedy totals
        """
        if not isinstance(violation_data, pd.DataFrame) or violation_data.empty:
            self.init_no_data_tab()
            return

        try:
            # Clear existing tabs
            while self.date_tabs.count():
                self.date_tabs.removeTab(0)
            self.models.clear()
            self.showing_no_data = False

            # Get all unique dates from column names
            all_dates = sorted(
                set(
                    col.split("_")[0]
                    for col in violation_data.columns
                    if "_" in col and col not in ["carrier_name", "list_status"]
                )
            )

            # Process each date
            for date in all_dates:
                date_data = pd.DataFrame()

                # Start with carrier info
                date_data["carrier_name"] = violation_data["carrier_name"]
                date_data["list_status"] = violation_data["list_status"]

                # Add each violation type's remedy total for this date
                for violation_type in self.VIOLATION_ORDER:
                    # Find the column for this date and violation type
                    col_name = next(
                        (
                            col
                            for col in violation_data.columns
                            if col.startswith(f"{date}_{violation_type}")
                            and not col.startswith(f"{date}_No Violation")
                        ),
                        None,
                    )
                    if col_name:
                        date_data[violation_type] = violation_data[col_name]
                    else:
                        date_data[violation_type] = 0

                # Add daily remedy total
                violation_columns = [
                    col for col in date_data.columns if col in self.VIOLATION_ORDER
                ]
                date_data["Remedy Total"] = (
                    date_data[violation_columns].sum(axis=1).round(2)
                )

                self.create_tab_for_date(date, date_data)

            # Create summary data
            summary_data = pd.DataFrame()

            # Start with carrier info
            summary_data["carrier_name"] = violation_data["carrier_name"]
            summary_data["list_status"] = violation_data["list_status"]

            # For each violation type, sum up all dates
            for violation_type in self.VIOLATION_ORDER:
                # Find all columns for this violation type
                violation_cols = [
                    col
                    for col in violation_data.columns
                    if "_" in col
                    and col.split("_", 1)[1].startswith(violation_type)
                    and not col.split("_", 1)[1].startswith("No Violation")
                ]
                if violation_cols:
                    summary_data[violation_type] = (
                        violation_data[violation_cols].sum(axis=1).round(2)
                    )
                else:
                    summary_data[violation_type] = 0

            # Add Weekly Remedy Total
            violation_columns = [
                col for col in summary_data.columns if col in self.VIOLATION_ORDER
            ]
            summary_data["Weekly Remedy Total"] = (
                summary_data[violation_columns].sum(axis=1).round(2)
            )

            # Add summary tab and make it active
            self.add_summary_tab(summary_data)
            self.date_tabs.setCurrentIndex(0)

        except Exception:
            traceback.print_exc()
            self.init_no_data_tab()
            return

    def add_summary_tab(self, data):
        """Create a summary tab showing weekly totals for all violation types.

        Args:
            data (pd.DataFrame): DataFrame with weekly violation totals
        """
        try:
            # Create model and view
            _, view = self.create_summary_model(data)

            # Add the tab
            tab_index = self.date_tabs.addTab(view, "Summary")

            # Calculate total violations for each list status
            carriers_with_violations = data[data["Weekly Remedy Total"] > 0]
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
            total_carriers = len(data)
            list_status_counts = data["list_status"].str.lower().value_counts()
            wal_carriers = list_status_counts.get("wal", 0)
            nl_carriers = list_status_counts.get("nl", 0)
            otdl_carriers = list_status_counts.get("otdl", 0)
            ptf_carriers = list_status_counts.get("ptf", 0)

            # Create the header text
            total_carriers_text = self.format_header_text(
                total_carriers, True
            ) + self.format_list_status_counts(
                wal_carriers, nl_carriers, otdl_carriers, ptf_carriers
            )

            carriers_violations_text = self.format_header_text(
                total_violations, False
            ) + self.format_list_status_counts(
                wal_violations, nl_violations, otdl_violations, ptf_violations
            )

            # Update the header with both rows
            self.update_violation_header(
                self.date_tabs,
                tab_index,
                total_violations,
                [total_carriers_text, carriers_violations_text],
            )

        except Exception:
            traceback.print_exc()

    def handle_tab_change(self, _):
        """Handle tab change events."""
        try:
            self.update_stats()
        except Exception:
            pass

    def handle_global_filter_click(self, status_type):
        """Handle global filter button clicks."""
        try:
            self.current_filter = status_type
            self.current_filter_type = "status"
            self.filter_carriers(status_type, "status")
        except Exception:
            pass
