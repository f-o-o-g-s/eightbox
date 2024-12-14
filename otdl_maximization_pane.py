"""Module for managing OTDL maximization tracking and Article 8.5.D compliance.

This module provides functionality for tracking overtime desired list (OTDL)
maximization requirements, specifically in relation to Article 8.5.D violations.
Key features include:

- OTDL carrier assignment tracking
- Overtime equitability monitoring
- Maximization status management per date
- Automatic excusal handling for:
  - Sundays
  - Sick leave
  - Annual leave
  - Holidays
  - NS protection
  - Guaranteed time
  - Hours at or above limit

The module primarily supports Article 8.5.D violation processing by:
- Tracking when OTDL was properly maximized
- Managing excusal data for non-violations
- Providing UI for reviewing and updating maximization status
- Syncing with carrier list updates

Note:
    This module specifically focuses on 8.5.D violations where non-OTDL carriers
    work overtime while OTDL carriers are available. The maximization status
    directly affects whether these incidents are counted as violations.
"""

from datetime import datetime
from functools import partial

import pandas as pd
from PyQt5.QtCore import (
    QEvent,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import CustomTitleBarWidget
from table_utils import setup_table_copy_functionality
from theme import (
    COLOR_NO_HIGHLIGHT,
    COLOR_ROW_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
)
from violation_model import calculate_optimal_gray


def is_automatically_excused(
    indicator,
    carrier_name=None,
    date=None,
    excusal_data=None,
    total=None,
    hour_limit=None,
):
    """Determine if a day should be automatically excused"""
    auto_excusal_indicators = {
        "(sick)",
        "(NS protect)",
        "(holiday)",
        "(guaranteed)",
        "(annual)",
    }

    # Get day of week for the date
    if date:
        day_of_week = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
        if day_of_week == "Sunday":
            if carrier_name and excusal_data is not None:
                excusal_data[(carrier_name, date)] = True
            return True

    # Automatically excuse if the indicator matches
    if indicator in auto_excusal_indicators:
        if carrier_name and date and excusal_data is not None:
            excusal_data[(carrier_name, date)] = True
        return True

    # Automatically excuse if total >= hour_limit
    if total is not None and hour_limit is not None and total >= hour_limit:
        if carrier_name and date and excusal_data is not None:
            excusal_data[(carrier_name, date)] = True
        return True

    return False


class OTDLMaximizationPane(QWidget):
    """Manages the Overtime Desired List (OTDL) maximization interface.

    Provides UI components and logic for analyzing and maximizing overtime
    distribution among carriers on the overtime desired list.
    """

    date_maximized_updated = pyqtSignal(str, bool)

    def __init__(self, parent=None, carrier_list_pane=None):
        super().__init__(parent)
        self.date_maximized = {}
        self.parent_widget = parent
        self.parent_main = parent

        print(
            f"OTDL pane initialized with carrier_list_pane: {carrier_list_pane is not None}"
        )

        # Connect to carrier list updates if available
        if carrier_list_pane:
            print("Connecting to carrier list updates in OTDL pane init")
            carrier_list_pane.carrier_list_updated.connect(
                self.handle_carrier_list_update
            )

        # Remove default window frame
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(title="OTDL Maximization", parent=self)
        main_layout.addWidget(self.title_bar)

        # Content widget to hold the table
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Add table to content layout
        self.table = QTableWidget()
        setup_table_copy_functionality(self.table)
        content_layout.addWidget(self.table)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)

        # Initialize tracking dictionaries
        self.violation_data = None
        self.date_maximized = {}
        self.cached_date_maximized = {}
        self.excusal_data = {}

        if self.parent_widget:
            self.date_maximized_updated.connect(
                self.parent_widget.handle_maximized_status_change
            )

        # Store reference to latest data
        self.clock_ring_data = None

        # Connect to carrier list updates if available
        if carrier_list_pane:
            carrier_list_pane.carrier_list_updated.connect(
                self.handle_carrier_list_update
            )

    def handle_carrier_list_update(self, updated_carrier_df):
        """Handle updates to the carrier list."""
        print("OTDL pane received carrier list update:")
        print(updated_carrier_df)
        if hasattr(self, "clock_ring_data") and self.clock_ring_data is not None:
            print("Refreshing OTDL view with updated carrier list")
            # Reset maximization state
            self.date_maximized = {}
            self.cached_date_maximized = {}
            self.excusal_data = {}
            # Refresh the data
            self.refresh_data(self.clock_ring_data, updated_carrier_df)
        else:
            print("No clock ring data available for refresh")

    def adjust_window_size(self):
        """Adjust the window size based on the table contents."""
        # Ensure all columns and rows are sized to their contents
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # Calculate total width needed
        width = (
            self.table.verticalHeader().width()  # Width of row headers
            + sum(
                [self.table.columnWidth(i) for i in range(self.table.columnCount())]
            )  # Sum of all column widths
            + 20
        )  # Reduced padding

        # Calculate total height needed including all rows
        total_row_height = 0
        for row in range(self.table.rowCount()):
            total_row_height += self.table.rowHeight(row)

        height = (
            self.table.horizontalHeader().height()  # Height of column headers
            + total_row_height  # Sum of all row heights
            + self.title_bar.height()  # Title bar height
            + 40
        )  # Reduced padding

        # Disable scrollbars
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set the final window size with minimal padding
        final_width = width + 10  # Minimal extra padding
        final_height = height + 10  # Minimal extra padding

        self.setFixedSize(final_width, final_height)

    def minimize_to_button(self):
        """Custom minimize handler that properly hides the window"""
        if self.parent_main and hasattr(self.parent_main, "otdl_button"):
            self.parent_main.otdl_button.setChecked(False)
        self.hide()

    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Prevent actual minimize, use our custom handler instead
                self.minimize_to_button()
                event.accept()
        super().changeEvent(event)

    def hideEvent(self, event):
        """Handle window hide events"""
        super().hideEvent(event)
        if self.parent_main and hasattr(self.parent_main, "otdl_button"):
            self.parent_main.otdl_button.setChecked(False)

    def set_violation_data(self, violation_data):
        """Set a copy of the violation data."""
        self.violation_data = violation_data
        print("Violation data set in OTDLMaximizationPane.")

    def apply_changes_for_date(self, date):
        """Apply maximized status changes for a specific date."""
        print(f"Applying changes for date: {date}")

        # Cache the current state
        self.cached_date_maximized = {
            key: value.copy() for key, value in self.date_maximized.items()
        }

        # Apply the changes
        if isinstance(self.date_maximized.get(date), dict):
            maximized_status = all(self.date_maximized[date].values())
            self.date_maximized[date]["is_maximized"] = maximized_status
        else:
            default_status = self.get_default_maximized_status(date)
            self.date_maximized[date] = {"is_maximized": default_status}

        # Update the UI
        self.update_maximized_status_row(date)

        # Emit the signal to notify the main app
        print(
            f"Emitting signal: date={date}, "
            f"maximized_status={self.date_maximized[date]['is_maximized']}"
        )
        self.date_maximized_updated.emit(
            date, self.date_maximized[date]["is_maximized"]
        )
        # Reload the cached state to keep toggles responsive
        self.reload_cached_state()

    def reload_cached_state(self):
        """Reload the cached state to allow further updates."""
        if self.cached_date_maximized:
            self.date_maximized = {
                key: value.copy() for key, value in self.cached_date_maximized.items()
            }

            # Update all rows to reflect the cached state
            for date in self.date_maximized.keys():
                self.update_maximized_status_row(date)

    def checkbox_state_changed(self, carrier_name, date, state):
        """Handle checkbox state changes for excusal."""
        excused = state == Qt.Checked

        # Ensure date_maximized[date] is a dictionary
        if not isinstance(self.date_maximized.get(date), dict):
            self.date_maximized[date] = {}

        # Update excusal data
        self.excusal_data[(carrier_name, date)] = excused
        self.date_maximized[date][carrier_name] = excused

        # Update the UI row color for the specific date
        self.update_maximized_status_row(date)

    def update_maximized_status_row(self, date=None):
        """Update the Maximized Status row for the given date."""
        maximized_row_index = (
            self.table.rowCount() - 2
        )  # Index for the Maximized Status row
        unique_dates = sorted(self.date_maximized.keys())

        if date:
            if date in unique_dates:
                col_idx = unique_dates.index(date) + 2  # Adjust for table layout
                carriers_excused = self.date_maximized.get(date, {})
                if not isinstance(carriers_excused, dict):
                    print(f"Error: self.date_maximized[{date}] is not a dictionary.")
                    return

                maximized_status = all(carriers_excused.values())
                status_text = f"Maximized: {maximized_status}"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                # Calculate background color based on row index
                maximized_row_color = (
                    COLOR_ROW_HIGHLIGHT
                    if maximized_row_index % 2 == 0
                    else COLOR_NO_HIGHLIGHT
                )
                status_item.setBackground(maximized_row_color)

                # Set text color based on maximized status
                if maximized_status:
                    status_item.setForeground(
                        QColor("#BB86FC")
                    )  # Material purple for True
                else:
                    # Use calculated optimal gray for false status
                    status_item.setForeground(
                        calculate_optimal_gray(maximized_row_color)
                    )

                self.table.setItem(maximized_row_index, col_idx, status_item)

        # Update all dates if no specific date is provided
        for col_idx, date in enumerate(unique_dates, start=2):
            carriers_excused = self.date_maximized.get(date, {})
            if not isinstance(carriers_excused, dict):
                print(f"Error: self.date_maximized[{date}] is not a dictionary.")
                continue

    def refresh_data(self, clock_ring_data, carrier_list_data):
        """Store latest clock ring data and refresh view."""
        self.clock_ring_data = clock_ring_data  # Store for future refreshes

        """Refresh the table with updated clock ring and carrier data."""
        # Filter for OTDL carriers
        otdl_data = carrier_list_data[carrier_list_data["list_status"] == "otdl"]
        otdl_names = otdl_data["carrier_name"].unique()

        # Filter clock ring data for OTDL carriers
        otdl_rings = clock_ring_data[
            clock_ring_data["carrier_name"].isin(otdl_names)
        ].copy()

        # Ensure numeric conversion for 'total' and 'leave_time'
        otdl_rings["total"] = pd.to_numeric(
            otdl_rings["total"], errors="coerce"
        ).fillna(0)
        otdl_rings["leave_time"] = pd.to_numeric(
            otdl_rings["leave_time"], errors="coerce"
        ).fillna(0)

        # Calculate daily_hours using the corrected numeric columns
        otdl_rings["daily_hours"] = otdl_rings.apply(
            lambda row: (
                max(row["total"], row["leave_time"])
                if row["leave_time"] <= row["total"]
                else row["total"] + row["leave_time"]
            ),
            axis=1,
        )

        # Get unique dates and sort them
        unique_dates = sorted(otdl_rings["rings_date"].unique())

        # Set up the table
        self.table.clear()
        self.table.setStyleSheet(
            f"background-color: {COLOR_NO_HIGHLIGHT.name()}; color: {COLOR_TEXT_LIGHT.name()};"
        )

        self.table.setRowCount(
            len(otdl_names) + 3
        )  # +3 for Day Names row, Maximized Status row, and Apply buttons
        self.table.setColumnCount(len(unique_dates) + 3)  # +3 for Weekly Hours

        # Set headers
        self.table.setHorizontalHeaderLabels(
            ["Carrier Name", "Hour Limit"] + unique_dates + ["Weekly Hours"]
        )
        # Set custom header colors
        header = self.table.horizontalHeader()
        header_bg = QColor("#37474F")  # Material Blue Grey 800
        header.setStyleSheet(
            f"""
            QHeaderView::section {{
                background-color: {header_bg.name()};
                color: {calculate_optimal_gray(header_bg).name()};
                padding: 8px;
                border: none;
                border-bottom: 2px solid #455A64;
                font-weight: bold;
            }}
        """
        )

        # Add Day Names Row
        day_name_row_index = 0  # Reserve row 0 for day names
        for col_idx, date in enumerate(
            unique_dates, start=2
        ):  # Skip first two columns (Carrier Name and Hour Limit)
            day_name = datetime.strptime(date, "%Y-%m-%d").strftime(
                "%A"
            )  # Convert date to day name
            day_name_item = QTableWidgetItem(day_name)
            day_name_item.setTextAlignment(Qt.AlignCenter)
            day_name_item.setFlags(Qt.ItemIsEnabled)  # Make the cell read-only
            font = day_name_item.font()
            font.setBold(True)
            font.setPointSize(10)  # Slightly larger than default
            day_name_item.setFont(font)
            # Use a slightly different shade for day names
            day_name_bg = QColor("#263238")  # Material Blue Grey 900
            day_name_item.setBackground(day_name_bg)
            day_name_item.setForeground(calculate_optimal_gray(day_name_bg))
            self.table.setItem(day_name_row_index, col_idx, day_name_item)

        # Initialize date_maximized dictionary
        self.date_maximized = {
            date: {} for date in unique_dates
        }  # Ensure all dates are included

        # Populate the table with carrier data (start from row 1)
        for row_idx, carrier in enumerate(otdl_names, start=1):  # Start from row 1
            # Calculate row color first
            row_color = COLOR_ROW_HIGHLIGHT if row_idx % 2 == 0 else COLOR_NO_HIGHLIGHT

            carrier_hours = otdl_rings[otdl_rings["carrier_name"] == carrier]
            carrier_name_item = QTableWidgetItem(carrier)
            carrier_name_item.setFlags(
                Qt.ItemIsSelectable | Qt.ItemIsEnabled
            )  # Non-editable
            carrier_name_item.setForeground(calculate_optimal_gray(row_color))
            carrier_name_item.setBackground(row_color)

            self.table.setItem(row_idx, 0, carrier_name_item)  # Carrier Name

            # Safely retrieve the hour limit for the carrier
            hour_limit = (
                otdl_data.loc[otdl_data["carrier_name"] == carrier, "hour_limit"].iloc[
                    0
                ]
                if not otdl_data.loc[
                    otdl_data["carrier_name"] == carrier, "hour_limit"
                ].empty
                else 12.00
            )

            # Ensure hour_limit is valid
            try:
                hour_limit_value = float(hour_limit) if hour_limit else 12.00
            except (ValueError, TypeError):
                print(
                    f"Invalid hour limit value: {hour_limit}, defaulting to 12.00 hours."
                )
                hour_limit_value = 12.00

            # Create and style Hour Limit column item
            hour_limit_item = QTableWidgetItem(f"{hour_limit_value:.2f}")
            hour_limit_item.setFlags(
                Qt.ItemIsSelectable | Qt.ItemIsEnabled
            )  # Non-editable
            hour_limit_item.setBackground(row_color)  # Keep alternating row color

            # Highlight non-default hour limits
            if hour_limit_value != 12.00:
                hour_limit_item.setForeground(QColor("#BB86FC"))  # Keep Material purple
            else:
                hour_limit_item.setForeground(
                    calculate_optimal_gray(row_color)
                )  # Replace COLOR_TEXT_DIM

            self.table.setItem(row_idx, 1, hour_limit_item)  # Set the Hour Limit column

            # Initialize weekly total hours and excusal status tracking
            weekly_hours = 0.0

            for col_idx, date in enumerate(unique_dates, start=2):
                day_data = carrier_hours.loc[carrier_hours["rings_date"] == date]
                if not day_data.empty:
                    daily_hours = day_data[
                        "daily_hours"
                    ].sum()  # Use daily_hours for calculations
                    weekly_hours += daily_hours  # Add to weekly total
                    indicator = day_data["display_indicators"].iloc[
                        0
                    ]  # Assign from data if available
                else:
                    daily_hours = 0.0
                    indicator = ""  # Default value when no data

                # Check if the day is automatically excused
                excused = is_automatically_excused(
                    indicator,
                    carrier,
                    date,
                    self.excusal_data,
                    daily_hours,
                    hour_limit_value,
                )
                self.date_maximized[date][carrier] = excused

                if excused:
                    value_text = f"{daily_hours:.2f} {indicator}".strip()
                    item = QTableWidgetItem(value_text)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setForeground(
                        calculate_optimal_gray(row_color)
                    )  # Replace COLOR_TEXT_LIGHT
                    # Use row_color instead of dark gray
                    item.setBackground(row_color)
                    self.table.setItem(row_idx, col_idx, item)
                    continue

                # For cells without checkboxes (regular days)
                if daily_hours >= hour_limit_value:
                    value_text = f"{daily_hours:.2f} {indicator}".strip()
                    item = QTableWidgetItem(value_text)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setForeground(
                        calculate_optimal_gray(row_color)
                    )  # Replace COLOR_TEXT_LIGHT
                    item.setBackground(row_color)  # Use alternating row color
                    self.table.setItem(row_idx, col_idx, item)
                    continue

                # For cells with checkboxes (potential violations)
                if daily_hours < hour_limit_value:
                    # Create checkbox with modern toggle switch style
                    checkbox = QCheckBox()
                    checkbox.setStyleSheet(
                        """
                        QCheckBox::indicator {
                            width: 30px;
                            height: 15px;
                            border: none;  /* Remove the white border */
                            background-color: #424242;  /* Unchecked color */
                        }
                        QCheckBox::indicator:checked {
                            background-color: #1976D2;  /* Material Blue when checked */
                        }
                        QCheckBox::indicator:unchecked {
                            background-color: #424242;  /* Dark grey when unchecked */
                        }
                    """
                    )

                    checkbox.setChecked(self.excusal_data.get((carrier, date), False))
                    checkbox.stateChanged.connect(
                        partial(self.checkbox_state_changed, carrier, date)
                    )

                    # Create a more compact layout
                    cell_widget = QWidget()
                    layout = QVBoxLayout(cell_widget)
                    layout.setContentsMargins(2, 2, 2, 2)  # Reduce margins
                    layout.setSpacing(2)  # Reduce spacing

                    # Add hours and indicator with black text
                    label = QLabel(f"{daily_hours:.2f} {indicator}".strip())
                    label.setStyleSheet("color: black;")  # Keep black text

                    # Create compact checkbox row with black text
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    checkbox_layout.setSpacing(2)
                    checkbox_layout.addWidget(checkbox)

                    # Make "Excuse?" text black
                    excuse_label = QLabel("Excuse?")
                    excuse_label.setStyleSheet("color: black;")
                    checkbox_layout.addWidget(excuse_label)
                    checkbox_layout.addStretch()

                    layout.addWidget(label)
                    layout.addWidget(checkbox_widget)

                    cell_widget.setLayout(layout)
                    cell_widget.setStyleSheet(
                        """
                        QWidget {
                            background-color: #d8b4fc;  /* Purple background */
                            border-radius: 3px;
                        }
                        """
                    )

                    self.table.setCellWidget(row_idx, col_idx, cell_widget)
                else:
                    value_text = f"{daily_hours:.2f} {indicator}".strip()
                    item = QTableWidgetItem(value_text)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setBackground(row_color)  # Use alternating row color
                    item.setForeground(
                        calculate_optimal_gray(row_color)
                    )  # Replace COLOR_TEXT_LIGHT
                    self.table.setItem(row_idx, col_idx, item)

            # Weekly Hours column styling
            weekly_hours_item = QTableWidgetItem(f"{weekly_hours:.2f}")
            weekly_hours_item.setTextAlignment(Qt.AlignCenter)
            weekly_hours_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            weekly_hours_item.setBackground(row_color)  # Use alternating row color
            weekly_hours_item.setForeground(
                calculate_optimal_gray(row_color)
            )  # Replace COLOR_TEXT_LIGHT
            self.table.setItem(row_idx, len(unique_dates) + 2, weekly_hours_item)

            # Add Maximized Status row
            maximized_row_index = (
                self.table.rowCount() - 2
            )  # Index for the Maximized Status row

            # Calculate the row color based on the maximized row index
            maximized_row_color = (
                COLOR_ROW_HIGHLIGHT
                if maximized_row_index % 2 == 0
                else COLOR_NO_HIGHLIGHT
            )

            for col_idx, date in enumerate(unique_dates, start=2):
                for carrier in otdl_names:
                    if carrier not in self.date_maximized[date]:
                        self.date_maximized[date][
                            carrier
                        ] = False  # Default to not excused

                carriers_excused = list(self.date_maximized[date].values())
                maximized_status = all(carriers_excused)

                status_text = f"Maximized: {maximized_status}"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                # Use the alternating row color as background
                status_item.setBackground(maximized_row_color)

                # Set text color based on maximized status
                if maximized_status:
                    status_item.setForeground(
                        QColor("#BB86FC")
                    )  # Keep Material purple for True
                else:
                    # Use calculated optimal gray instead of COLOR_TEXT_DIM
                    status_item.setForeground(
                        calculate_optimal_gray(maximized_row_color)
                    )

                self.table.setItem(maximized_row_index, col_idx, status_item)

        # Add Apply buttons row
        apply_row_index = self.table.rowCount() - 1  # Index for the Apply buttons row
        for col_idx, date in enumerate(unique_dates, start=2):
            apply_button = QPushButton("Apply")
            apply_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: #2D2D2D;
                    color: #BB86FC;
                    border: 1px solid #3D3D3D;
                    border-bottom: 2px solid #1D1D1D;
                    padding: 4px 16px;
                    font-weight: 500;
                    min-height: 26px;
                    border-radius: 3px;
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background-color: #353535;
                    border: 1px solid #454545;
                    border-bottom: 2px solid #252525;
                    color: #CBB0FF;
                }}
                QPushButton:pressed {{
                    background-color: #252525;
                    border: 1px solid #353535;
                    border-top: 2px solid #151515;
                    border-bottom: 1px solid #353535;
                    padding-top: 5px;
                    color: #BB86FC;
                }}
                QPushButton:disabled {{
                    background-color: #252525;
                    color: {calculate_optimal_gray(QColor('#252525')).name()};
                    border: 1px solid #2D2D2D;
                }}
                """
            )
            apply_button.clicked.connect(partial(self.apply_changes_for_date, date))
            self.table.setCellWidget(apply_row_index, col_idx, apply_button)
        self.adjust_window_size()

    def get_excused_carriers(self, date):
        """Get list of excused carriers for a given date.

        Args:
            date (str): Date in YYYY-MM-DD format

        Returns:
            list: List of carrier names who are excused from working to their hour limit
        """
        excused_carriers = []

        # Check if we have excusal data for this date
        if date in self.date_maximized:
            # Get all carriers marked as excused
            for carrier_name, excused in self.date_maximized[date].items():
                if carrier_name != "is_maximized" and excused:
                    excused_carriers.append(carrier_name)

        return excused_carriers
