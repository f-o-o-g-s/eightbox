import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)


class Violation85fNsTab(BaseViolationTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = "85f_ns"

    def create_tab_for_date(self, date, date_data):
        """Create a tab for the given date."""
        # Filter to display columns
        display_columns = [
            "carrier_name",
            "list_status",
            "violation_type",
            "date",
            "remedy_total",
            "total_hours",
        ]
        filtered_data = date_data[display_columns]

        model = ViolationModel(filtered_data, tab_type=self.tab_type, is_summary=False)
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
            "list_status",
            "date",
            "violation_type",
            "remedy_total",
            "total_hours",
            "own_route_hours",
            "off_route_hours",
            "moves",
        ]
        for col in required_columns:
            if col not in violation_data.columns:
                violation_data[col] = pd.NA

        # Round numerical columns
        numerical_columns = ["remedy_total", "total_hours"]
        for col in numerical_columns:
            if col in violation_data.columns:
                violation_data[col] = violation_data[col].round(2)

        violation_data = violation_data.dropna(subset=["date"])

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
        """Add or update the summary tab with aggregated data."""
        # Get carrier statuses
        carrier_status = data.groupby("carrier_name")["list_status"].first()

        # Calculate weekly totals
        weekly_totals = data.groupby("carrier_name")["remedy_total"].sum().round(2)

        # Get daily totals
        daily_totals = data.pivot_table(
            index="carrier_name",
            columns="date",
            values="remedy_total",
            aggfunc="sum",
            fill_value=0,
        )

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
