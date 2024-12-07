import pandas as pd

from base_violation_tab import BaseViolationTab
from utils import set_display
from violation_model import ViolationFilterProxyModel, ViolationModel


class ViolationMAX60Tab(BaseViolationTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = "MAX60"

    def create_tab_for_date(self, date, date_data):
        """Create a tab for the given date."""
        # Format daily hours with display indicator
        date_data = date_data.copy()
        date_data["daily_hours"] = date_data.apply(
            lambda row: (
                f"{row['daily_hours']:.2f} {row['display_indicator']}"
                if pd.notna(row["daily_hours"])
                else row["display_indicator"]
            ),
            axis=1,
        )

        # Reorder columns for display
        display_columns = [
            "carrier_name",
            "list_status",
            "date",
            "daily_hours",
            "cumulative_hours",
            "remedy_total",
            "violation_type",
        ]
        date_data = date_data[display_columns]

        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

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
            "daily_hours",
            "list_status",
            "leave_type",
            "code",
            "cumulative_hours",
            "remedy_total",
            "violation_type",
            "display_indicator",
            "total",
        ]
        for col in required_columns:
            if col not in violation_data.columns:
                violation_data[col] = pd.NA

        # Generate display_indicator if not present
        if "display_indicator" not in violation_data.columns:
            violation_data["display_indicator"] = violation_data.apply(
                set_display, axis=1
            )

        violation_data = violation_data.dropna(subset=["date"])

        # Round numerical columns
        numerical_columns = ["remedy_total", "daily_hours", "cumulative_hours"]
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
        """Add a summary tab with daily hours for each carrier."""
        # Get unique dates for columns
        unique_dates = sorted(data["date"].unique())

        # Create base summary data with carrier names and list status
        summary_data = (
            data.groupby("carrier_name")
            .first()
            .reset_index()[["carrier_name", "list_status"]]
        )

        # Add daily hours with display indicators for each date
        for date in unique_dates:
            date_data = data[data["date"] == date].copy()
            summary_data[date] = (
                summary_data["carrier_name"]
                .map(
                    date_data.set_index("carrier_name").apply(
                        lambda row: (
                            f"{row['daily_hours']:.2f} {row['display_indicator']}"
                            if pd.notna(row["daily_hours"])
                            else row["display_indicator"]
                        ),
                        axis=1,
                    )
                )
                .fillna("")
            )

        # Add remedy_total and cumulative_hours
        remedy_totals = data.groupby("carrier_name")["remedy_total"].sum().round(2)
        cumulative_hours = (
            data.groupby("carrier_name")["cumulative_hours"].max().round(2)
        )

        summary_data["remedy_total"] = summary_data["carrier_name"].map(remedy_totals)
        summary_data["cumulative_hours"] = summary_data["carrier_name"].map(
            cumulative_hours
        )

        # Reorder columns to include list_status
        pivot_columns = (
            ["carrier_name", "list_status", "remedy_total"]
            + unique_dates
            + ["cumulative_hours"]
        )
        summary_data = summary_data[pivot_columns]
        summary_data.rename(
            columns={"remedy_total": "Weekly Remedy Total"}, inplace=True
        )

        # Create model and view
        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.summary_proxy_model = proxy_model
        self.date_tabs.addTab(view, "Summary")
