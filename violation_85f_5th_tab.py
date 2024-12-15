"""Implementation of Article 8.5.F fifth overtime day violation tracking tab.

This module provides specific implementations for tracking and displaying
Article 8.5.F violations that occur when non-OTDL carriers work overtime
on more than 4 of their 5 scheduled days in a service week.
"""

import pandas as pd
from PyQt5.QtWidgets import QTableView

from base_violation_tab import BaseViolationTab
from utils import set_display
from violation_model import ViolationModel
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
            formatted_data["display_indicator"] = formatted_data.apply(
                set_display, axis=1
            )

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

    def configure_tab_view(self, view, model: ViolationModel):
        """Configure the tab view after creation.

        Hides the violation_dates column which is only used internally.

        Args:
            view: The widget containing the table view
            model: The model containing the data
        """
        # Get the actual QTableView from the widget
        table_view = None
        if isinstance(view, QTableView):
            table_view = view
        elif hasattr(view, "findChild"):
            table_view = view.findChild(QTableView)

        if table_view and "violation_dates" in model.df.columns:
            column_idx = model.df.columns.get_loc("violation_dates")
            table_view.setColumnHidden(column_idx, True)

    def create_table_view(self, model, proxy_model=None):
        """Create and configure a table view for the violation data.

        Overrides base class method to hide the 85F_5th_date column.
        """
        view = super().create_table_view(model, proxy_model)

        # Hide the 85F_5th_date column immediately after view creation
        if isinstance(view, QTableView) and "85F_5th_date" in model.df.columns:
            column_idx = model.df.columns.get_loc("85F_5th_date")
            view.setColumnHidden(column_idx, True)

        return view

    def add_summary_tab(self, data):
        """Create or update the summary tab with weekly violation totals.
        Shows total hours for daily columns but keeps Weekly Remedy Total.

        The 85F_5th_date column is kept in the model for highlighting logic
        but is excluded from the view for cleaner presentation.

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

        # Get the 85F_5th_date for each carrier by finding the 5th overtime day
        def get_violation_date(group):
            ot_days = group[group["total_hours"] > 8.0]
            if len(ot_days) >= 5:
                return ot_days.sort_values(date_column)["85F_5th_date"].iloc[4]
            return None

        fifth_dates = data.groupby("carrier_name").apply(get_violation_date)

        # Combine all data including 85F_5th_date for the model
        summary_data = pd.concat(
            [
                carrier_status.rename("list_status"),
                weekly_totals.rename("Weekly Remedy Total"),
                fifth_dates.rename("85F_5th_date"),
                daily_totals,
            ],
            axis=1,
        ).reset_index()

        # Round numerical columns
        for col in summary_data.columns:
            if col not in ["carrier_name", "list_status", "85F_5th_date"]:
                summary_data.loc[:, col] = summary_data[col].round(2)

        # Create display data without 85F_5th_date column
        display_columns = [col for col in summary_data.columns if col != "85F_5th_date"]
        display_data = summary_data[display_columns].copy()

        # Create model with display data and add back 85F_5th_date for highlighting
        model = ViolationModel(display_data, tab_type=self.tab_type, is_summary=True)
        model.df["85F_5th_date"] = summary_data["85F_5th_date"]

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
