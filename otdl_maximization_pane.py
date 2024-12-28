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
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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

    date_maximized_updated = pyqtSignal(str, object)

    def __init__(self, parent=None, carrier_list_pane=None):
        super().__init__(parent)
        self.date_maximized = {}
        self.parent_widget = parent
        self.parent_main = parent

        # Connect to carrier list updates if available
        if carrier_list_pane:
            carrier_list_pane.carrier_list_updated.connect(
                self.handle_carrier_list_update
            )

        # Remove default window frame
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(title="OTDL Maximization", parent=self)
        main_layout.addWidget(self.title_bar)

        # Create a central widget to hold both the table and footer
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(2, 2, 2, 0)  # Remove bottom margin
        central_layout.setSpacing(0)

        # Create a scroll area for the table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame border
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create table container widget
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(2, 2, 2, 2)
        table_layout.setSpacing(0)

        # Add table to table container
        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultSectionSize(100)

        setup_table_copy_functionality(self.table)
        table_layout.addWidget(self.table)

        # Set table container as the scroll area widget
        scroll_area.setWidget(table_container)

        # Create a widget to hold the scroll area
        scroll_container = QWidget()
        scroll_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_layout.addWidget(scroll_area)

        central_layout.addWidget(scroll_container, 1)  # Add stretch factor of 1

        # Create sticky footer with separator
        footer = QWidget()
        footer.setObjectName("footer")
        footer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Fixed height
        footer.setStyleSheet(
            """
            QWidget#footer {
                background-color: #1E1E1E;
                border-top: 1px solid #333333;
                min-height: 60px;
                max-height: 60px;
                padding-bottom: 8px;  /* Add margin at the bottom */
            }
        """
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 10, 10, 10)

        # Create Apply button with existing style
        apply_button = QPushButton("Apply All Changes")
        apply_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #2D2D2D;
                color: #BB86FC;
                border: 1px solid #3D3D3D;
                border-bottom: 2px solid #1D1D1D;
                padding: 8px 24px;
                font-weight: 500;
                min-height: 32px;
                border-radius: 4px;
                font-size: 14px;
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
                padding-top: 9px;
                color: #BB86FC;
            }}
            QPushButton:disabled {{
                background-color: #252525;
                color: {calculate_optimal_gray(QColor('#252525')).name()};
                border: 1px solid #2D2D2D;
            }}
            """
        )
        apply_button.clicked.connect(self.apply_all_changes)
        footer_layout.addStretch()
        footer_layout.addWidget(apply_button)
        footer_layout.addStretch()

        # Add footer to central layout with no stretch
        central_layout.addWidget(footer, 0)  # No stretch factor

        # Add central widget to main layout
        main_layout.addWidget(central_widget)

        # Initialize tracking dictionaries
        self.violation_data = None
        self.date_maximized = {}
        self.cached_date_maximized = {}
        self.excusal_data = {}

        # Store reference to latest data
        self.clock_ring_data = None

        # Connect to carrier list updates if available
        if carrier_list_pane:
            carrier_list_pane.carrier_list_updated.connect(
                self.handle_carrier_list_update
            )

    def handle_carrier_list_update(self, updated_carrier_df):
        """Handle updates to the carrier list."""
        if hasattr(self, "clock_ring_data") and self.clock_ring_data is not None:
            # Reset maximization state
            self.date_maximized = {}
            self.cached_date_maximized = {}
            self.excusal_data = {}
            # Refresh the data
            self.refresh_data(self.clock_ring_data, updated_carrier_df)

    def adjust_window_size(self):
        """Adjust the window size based on the table contents."""
        # Clear any previous size constraints
        self.setMinimumSize(0, 0)

        # Ensure all columns and rows are sized to their contents
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # Calculate total width needed
        width = (
            self.table.verticalHeader().width()  # Width of row headers
            + sum(
                [self.table.columnWidth(i) for i in range(self.table.columnCount())]
            )  # Sum of all column widths
            + 20  # Minimal padding
        )

        # Calculate total height needed
        total_height = (
            self.title_bar.height()  # Title bar height
            + self.table.horizontalHeader().height()  # Header height
            + sum(
                [self.table.rowHeight(i) for i in range(self.table.rowCount())]
            )  # Content height
            + 60  # Footer height
            + 20  # Padding
        )

        # Get screen dimensions
        screen = QApplication.primaryScreen().availableGeometry()

        # Cap width at 90% of screen width if needed
        if width > screen.width() * 0.9:
            width = int(screen.width() * 0.9)

        # Cap height at 90% of screen height if needed
        if total_height > screen.height() * 0.9:
            total_height = int(screen.height() * 0.9)

        # Set the final window size
        self.setFixedSize(width, total_height)

        # Update scroll area if content exceeds window size
        if total_height >= screen.height() * 0.9:
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def minimize_to_button(self):
        """Custom minimize handler that properly hides the window"""
        if self.parent_main and hasattr(self.parent_main, "otdl_button"):
            self.parent_main.otdl_button.setChecked(False)
        self.hide()

    def change_event(self, event):
        """Handle window state changes"""
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Prevent actual minimize, use our custom handler instead
                self.minimize_to_button()
                event.accept()
        super().change_event(event)

    def hide_event(self, event):
        """Handle window hide events"""
        super().hide_event(event)
        if self.parent_main and hasattr(self.parent_main, "otdl_button"):
            self.parent_main.otdl_button.setChecked(False)

    def set_violation_data(self, violation_data):
        """Set a copy of the violation data."""
        self.violation_data = violation_data

    def apply_all_changes(self):
        """Gather all maximization changes and emit them as a batch."""
        # Check if there's any data to process
        if (
            not hasattr(self, "clock_ring_data")
            or self.clock_ring_data is None
            or self.clock_ring_data.empty
        ):
            return

        # Cache the current state
        self.cached_date_maximized = {
            key: value.copy() for key, value in self.date_maximized.items()
        }

        # Gather all changes
        changes = {}
        for date in sorted(self.date_maximized.keys()):
            # Get all excused carriers for this date
            excused_carriers = self.get_excused_carriers(date)

            # Get all OTDL carriers for this date
            otdl_carriers = set()
            date_data = self.clock_ring_data[self.clock_ring_data["rings_date"] == date]
            otdl_carriers = set(
                date_data[date_data["list_status"] == "otdl"]["carrier_name"].unique()
            )

            # A date is maximized if all OTDL carriers are excused
            maximized_status = len(otdl_carriers) > 0 and all(
                str(carrier) in excused_carriers for carrier in otdl_carriers
            )

            # Store the change
            changes[date] = {
                "is_maximized": maximized_status,
                "excused_carriers": excused_carriers,
            }

            # Update internal state
            if isinstance(self.date_maximized.get(date), dict):
                self.date_maximized[date]["is_maximized"] = maximized_status
            else:
                self.date_maximized[date] = {"is_maximized": maximized_status}

        # Only emit signal if we have changes
        if changes:
            self.date_maximized_updated.emit("all", changes)
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
        self.excusal_data[(str(carrier_name), str(date))] = excused
        self.date_maximized[str(date)][str(carrier_name)] = excused

        # Update the UI row color for the specific date
        self.update_maximized_status_row(date)

    def update_maximized_status_row(self, date=None):
        """Update the maximized status in the internal state without UI updates."""
        unique_dates = sorted(self.date_maximized.keys())

        if date and date in unique_dates:
            carriers_excused = self.date_maximized.get(date, {})
            if not isinstance(carriers_excused, dict):
                return

            # Update internal state only
            maximized_status = all(carriers_excused.values())
            if isinstance(self.date_maximized[date], dict):
                self.date_maximized[date]["is_maximized"] = maximized_status

        # Update all dates if no specific date is provided
        for date in unique_dates:
            carriers_excused = self.date_maximized.get(date, {})
            if not isinstance(carriers_excused, dict):
                continue

            # Update internal state only
            maximized_status = all(carriers_excused.values())
            if isinstance(self.date_maximized[date], dict):
                self.date_maximized[date]["is_maximized"] = maximized_status

    def refresh_data(self, clock_ring_data, carrier_list_data):
        """Store latest clock ring data and refresh view."""
        self.clock_ring_data = clock_ring_data  # Store for future refreshes

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

        # Clear existing table
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        # Clear any size constraints
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX

        # Set up the table
        self.table.setStyleSheet(
            f"background-color: {COLOR_NO_HIGHLIGHT.name()}; color: {COLOR_TEXT_LIGHT.name()};"
        )

        # Set row count: carriers + day names row
        self.table.setRowCount(len(otdl_names) + 1)
        self.table.setColumnCount(
            len(unique_dates) + 3
        )  # +3 for Carrier Name, Hour Limit, Weekly Hours

        # Set headers
        self.table.setHorizontalHeaderLabels(
            ["Carrier Name", "Hour Limit"] + unique_dates + ["Weekly Hours"]
        )
        # Set custom header colors
        header = self.table.horizontalHeader()
        header_bg = QColor("#37474F")  # Material Blue Grey 800

        # Set resize modes for columns
        header.setSectionResizeMode(
            QHeaderView.Interactive
        )  # Default mode for all columns
        header.setSectionResizeMode(
            len(unique_dates) + 2, QHeaderView.Stretch
        )  # Make Weekly Hours column stretch

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
                    indicator = day_data["display_indicator"].iloc[
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

        # Adjust window size after populating data
        self.adjust_window_size()

        # If no data, set a reasonable minimum size
        if len(otdl_names) == 0:
            self.resize(400, 300)

    def get_excused_carriers(self, date):
        """Get list of excused carriers for a given date.

        This includes carriers who are:
        - Manually excused via checkbox
        - Automatically excused due to:
            - Sundays
            - Sick leave
            - Annual leave
            - Holidays
            - NS protection
            - Guaranteed time
            - Already at/above their hour limit

        Args:
            date (str): Date in YYYY-MM-DD format

        Returns:
            list: List of carrier names who are excused from working to their hour limit
        """
        excused_carriers = set()  # Use a set to avoid duplicates

        # Get all carriers who are manually excused via checkbox from date_maximized
        if date in self.date_maximized:
            for carrier_name, excused in self.date_maximized[date].items():
                if carrier_name != "is_maximized" and excused:
                    excused_carriers.add(str(carrier_name))

        # Check excusal_data dictionary for manual excusals
        for (carrier, excusal_date), excused in self.excusal_data.items():
            if excusal_date == date and excused:
                excused_carriers.add(str(carrier))

        # Get carriers who are automatically excused
        if self.clock_ring_data is not None:
            date_data = self.clock_ring_data[self.clock_ring_data["rings_date"] == date]

            for _, row in date_data.iterrows():
                carrier_name = str(row["carrier_name"])

                # Get indicator and hours
                indicator = row.get("display_indicator", "")  # Use singular form
                total_hours = pd.to_numeric(row.get("total", 0), errors="coerce")
                hour_limit = pd.to_numeric(
                    row.get("hour_limit", 12.00), errors="coerce"
                )

                # Check if automatically excused
                if is_automatically_excused(
                    indicator,
                    carrier_name=carrier_name,
                    date=date,
                    excusal_data=self.excusal_data,
                    total=total_hours,
                    hour_limit=hour_limit,
                ):
                    excused_carriers.add(carrier_name)

        # Convert all carrier names to strings and return as sorted list
        return sorted(excused_carriers)

    def hideEvent(self, event):
        """Handle hide event by unchecking the corresponding button."""
        if hasattr(self.parent_main, "otdl_maximization_button"):
            self.parent_main.otdl_maximization_button.setChecked(False)
        super().hideEvent(event)
