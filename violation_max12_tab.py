"""Implementation of the Maximum 12-Hour Rule violation tracking tab.

This module provides specific implementation for tracking and displaying
violations of the 12-hour work limit, which prohibits carriers from working
more than 12 hours in a single day (11.50 hours for WAL carriers).
"""

from base_violation_tab import BaseViolationTab
from violation_model import (
    ViolationFilterProxyModel,
    ViolationModel,
)
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

    def create_tab_for_date(self, date, date_data):
        """Create a tab showing violations for a specific date.

        Args:
            date (datetime.date): The date to display
            date_data (pd.DataFrame): Violation data for the specified date

        Returns:
            QTableView: The configured view for the new tab

        Note:
            Displays carrier name, list status, total hours worked,
            and remedy hours (hours beyond 12.00 or 11.50).
        """
        model = ViolationModel(date_data, tab_type=self.tab_type, is_summary=False)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.models[date] = {"model": model, "proxy": proxy_model, "tab": view}

        self.date_tabs.addTab(view, str(date))
        return view

    def refresh_data(self, violation_data):
        """Refresh all tabs with new violation data.

        Clears existing tabs and creates new ones based on the provided data.
        Handles data preprocessing including:
        - Column validation and creation
        - NaN handling
        - Numerical rounding to 2 decimal places
        - Tab state management

        Args:
            violation_data (pd.DataFrame): New violation data containing:
                - carrier_name: Name of the carrier
                - date: Date of potential violation
                - total_hours: Total hours worked that day
                - own_route_hours: Hours on assigned route
                - off_route_hours: Hours on other routes
                - moves: Number of route changes
                - remedy_total: Hours beyond limit

        Note:
            Creates a tab for each date and a summary tab showing
            weekly totals. Shows "No Data" tab if violation_data is empty.
        """
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
            "own_route_hours",
            "off_route_hours",
            "moves",
        ]
        for col in required_columns:
            if col not in violation_data.columns:
                violation_data[col] = ""

        violation_data = violation_data.dropna(subset=["date"])

        # Round numerical columns
        numerical_columns = [
            "remedy_total",
            "total_hours",
            "own_route_hours",
            "off_route_hours",
        ]
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
        """Create or update the summary tab with weekly violation totals.

        Creates a summary view showing:
        - Carrier list status
        - Weekly total of remedy hours
        - Daily total hours worked
        - All values rounded to 2 decimal places

        Args:
            data (pd.DataFrame): Complete violation data for the week

        Note:
            Aggregates data by carrier, showing their daily hours and
            total remedy hours for the week. NaN values are replaced
            with 0 for clarity.
        """
        # Get unique carriers and their list_status
        summary_data = data.groupby("carrier_name")["list_status"].first().reset_index()

        # Add remedy_total as Weekly Remedy Total
        remedy_totals = data.groupby("carrier_name")["remedy_total"].sum().round(2)
        summary_data = summary_data.merge(
            remedy_totals.rename("Weekly Remedy Total"), on="carrier_name", how="left"
        )

        # Add total_hours for each unique date as a separate column
        unique_dates = sorted(data["date"].unique())
        for date in unique_dates:
            date_hours = (
                data[data["date"] == date]
                .groupby("carrier_name")["total_hours"]
                .sum()
                .round(2)
            )
            summary_data = summary_data.merge(
                date_hours.rename(date), on="carrier_name", how="left"
            )

        # Replace NaN with 0 for clarity
        summary_data.fillna(0, inplace=True)

        # Create model and view
        model = ViolationModel(summary_data, tab_type=self.tab_type, is_summary=True)
        proxy_model = ViolationFilterProxyModel()
        proxy_model.setSourceModel(model)
        view = self.create_table_view(model, proxy_model)

        self.summary_proxy_model = proxy_model
        self.date_tabs.addTab(view, "Summary")
