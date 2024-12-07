import pandas as pd

from base_violation_tab import BaseViolationTab
from violation_model import ViolationFilterProxyModel, ViolationModel


class ViolationRemediesTab(BaseViolationTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_type = "ViolationRemedies"

    def create_tab_for_date(self, date, date_data):
        """Create a tab for the given date."""
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
        """Refresh the tabs with remedies data."""
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
        """Add a single summary tab showing aggregated violations."""
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
