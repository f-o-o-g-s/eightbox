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
        """Create a tab for the given date."""
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

    def refresh_data(self, violation_data):
        """Refresh all tabs with new violation data."""
        if violation_data.empty:
            self.init_no_data_tab()
            return

        current_tab_index = self.date_tabs.currentIndex()
        current_tab_name = self.date_tabs.tabText(current_tab_index)

        while self.date_tabs.count():
            self.date_tabs.removeTab(0)
        self.models.clear()
        self.showing_no_data = False

        # Ensure required columns exist
        required_columns = [
            "carrier_name",
            "date",
            "violation_type",
            "remedy_total",
            "total_hours",
            "display_indicator",
            "85F_5th_date",
        ]
        for col in required_columns:
            if col not in violation_data.columns:
                violation_data[col] = ""

        # Add display_indicator if not present
        if "display_indicator" not in violation_data.columns:
            violation_data["display_indicator"] = violation_data.apply(
                set_display, axis=1
            )

        violation_data = violation_data.dropna(subset=["date"])

        # Round numerical columns
        numerical_columns = ["remedy_total", "total_hours"]
        for col in numerical_columns:
            if col in violation_data.columns:
                violation_data[col] = violation_data[col].round(2)

        # Create tabs for each date
        for date in sorted(violation_data["date"].unique()):
            date_data = violation_data[violation_data["date"] == date]
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

    def add_summary_tab(self, data):
        """Add a summary tab that displays carrier totals and daily hours for a 7-day range."""
        unique_dates = sorted(data["date"].unique())

        # Create base summary data with carrier names and list status
        summary_data = (
            data.groupby("carrier_name")
            .first()
            .reset_index()[["carrier_name", "list_status"]]
        )

        # Add daily hours with indicators
        for date in unique_dates:
            summary_data[date] = (
                summary_data["carrier_name"]
                .map(
                    lambda carrier: data[
                        (data["carrier_name"] == carrier) & (data["date"] == date)
                    ]
                    .apply(
                        lambda row: (
                            f"{row['total_hours']:.2f} {row['display_indicator']}"
                            if pd.notna(row["total_hours"])
                            else row["display_indicator"]
                        ),
                        axis=1,
                    )
                    .sum()
                )
                .fillna("")
            )

        # Add remedy total and violation dates
        remedy_totals = data.groupby("carrier_name")["remedy_total"].sum().round(2)
        violation_dates = data.groupby("carrier_name")["85F_5th_date"].agg(
            lambda x: list(x[x != ""].unique())
        )

        summary_data["remedy_total"] = summary_data["carrier_name"].map(remedy_totals)
        summary_data["violation_dates"] = summary_data["carrier_name"].map(
            violation_dates
        )

        # Reorder columns
        pivot_columns = [
            "carrier_name",
            "list_status",
            "remedy_total",
            "violation_dates",
        ] + unique_dates
        summary_data = summary_data[pivot_columns]

        # Rename columns
        summary_data.rename(
            columns={
                "carrier_name": "Carrier Name",
                "list_status": "List Status",
                "remedy_total": "Weekly Remedy Total",
            },
            inplace=True,
        )

        # Create model and view
        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        # Hide violation_dates column
        if "violation_dates" in model.df.columns:
            column_idx = model.df.columns.get_loc("violation_dates")
            view.setColumnHidden(column_idx, True)

        self.summary_proxy_model = proxy_model
        self.date_tabs.addTab(view, "Summary")
