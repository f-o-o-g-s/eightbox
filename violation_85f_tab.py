import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)


class Violation85fTab(BaseViolationTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = "85F"

    def create_tab_for_date(self, date, date_data):
        """Create a tab for the given date."""
        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view

    def add_summary_tab(self, data):
        """Add or update the summary tab with aggregated data."""
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
