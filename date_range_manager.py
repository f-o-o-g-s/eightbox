"""Date range management and processing functionality.

This module handles all date range related operations including:
- Applying date ranges and processing violations
- Updating OTDL violations
- Managing maximization status changes
- Handling carrier data updates
- Managing tab data clearing
"""

import json
import os
import traceback

import pandas as pd
from PyQt5.QtCore import (
    QObject,
    Qt,
    QTimer,
)
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
)

from custom_widgets import (
    CustomInfoDialog,
    CustomProgressDialog,
)
from otdl_maximization_pane import OTDLMaximizationPane
from violation_detection import (
    detect_violations,
    get_violation_remedies,
)


class DateRangeManager(QObject):
    """Manages date range operations and violation processing.

    This class encapsulates all date range related functionality that was
    previously in the main application class. It maintains references to
    necessary UI components while providing a cleaner separation of concerns.

    Args:
        main_app: Reference to the main application instance
    """

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.violations = {}

    def retry_apply_date_range(self):
        """Retry apply_date_range after carrier list is saved."""
        # Disconnect the one-time signal
        if (
            hasattr(self.main_app, "carrier_list_pane")
            and self.main_app.carrier_list_pane is not None
        ):
            try:
                self.main_app.carrier_list_pane.data_updated.disconnect()
            except TypeError:  # In case it's already disconnected
                pass

        # Check if carrier_list.json exists and is valid before proceeding
        if os.path.exists("carrier_list.json"):
            try:
                with open(
                    "carrier_list.json", "r", encoding="utf-8"
                ) as json_file:  # Added encoding
                    carrier_list = pd.DataFrame(json.load(json_file))
                    if not carrier_list.empty:
                        # Small delay to ensure UI updates are complete
                        QTimer.singleShot(100, self.apply_date_range)
            except Exception:
                pass  # If there's an error, just don't retry

    def clear_tabs_and_data(self):
        """Clear all existing tabs and reset associated data."""
        print("Clearing all tabs and resetting data for the new date range.")

        # Remove all tabs from the central tab widget
        while self.main_app.central_tab_widget.count() > 0:
            self.main_app.central_tab_widget.removeTab(0)

        # Reset all tab references to None
        self.main_app.vio_85d_tab = None
        self.main_app.vio_85f_tab = None
        self.main_app.vio_85f_ns_tab = None
        self.main_app.vio_85f_5th_tab = None
        self.main_app.vio_85g_tab = None
        self.main_app.vio_MAX12_tab = None
        self.main_app.vio_MAX60_tab = None
        self.main_app.remedies_tab = None

        # Reset other associated data
        self.main_app.current_data = pd.DataFrame()
        self.violations = None

    def on_carrier_data_updated(self, _):
        """Handle updates to the carrier list and refresh all tabs.

        Actually uses the JSON file for applying updates to the fetched clock ring data.
        Just updating the data without clicking 'Save Carrier List' will not update the views.
        """
        print("DateRangeManager: Received data_updated signal.")

        # Load the most up-to-date carrier data from the JSON file
        try:
            with open("carrier_list.json", "r", encoding="utf-8") as json_file:
                carrier_list = pd.DataFrame(json.load(json_file))
        except FileNotFoundError:
            QMessageBox.critical(self.main_app, "Error", "carrier_list.json not found.")
            return
        except Exception as e:
            QMessageBox.critical(
                self.main_app, "Error", f"Failed to load carrier_list.json: {str(e)}"
            )
            return

        # Fetch clock ring data from the database
        clock_ring_data = self.main_app.fetch_clock_ring_data()
        if not clock_ring_data.empty:
            # Merge clock ring data with the carrier list from JSON
            clock_ring_data = clock_ring_data.merge(
                carrier_list[["carrier_name", "list_status"]],
                on="carrier_name",
                how="left",
                suffixes=("_db", "_updated"),
            )

            # Consolidate list_status
            clock_ring_data["list_status"] = clock_ring_data[
                "list_status_updated"
            ].combine_first(clock_ring_data["list_status_db"])
            clock_ring_data.drop(
                columns=["list_status_db", "list_status_updated"], inplace=True
            )

        # Refresh other components
        if self.main_app.otdl_maximization_pane:
            print("Refreshing OTDLMaximizationPane with updated data.")
            self.main_app.otdl_maximization_pane.refresh_data(
                clock_ring_data, carrier_list
            )

        # Update violations and remedies
        self.update_violations_and_remedies(clock_ring_data)

    def apply_date_range(self):
        """Apply the selected date range and process violations."""
        # First check: Database path validation
        if not os.path.exists(self.main_app.mandates_db_path):
            CustomInfoDialog.information(
                self.main_app,
                "Database Not Found",
                "Please configure the database path before proceeding.",
            )
            self.main_app.open_settings_dialog()
            if (
                hasattr(self.main_app, "carrier_list_pane")
                and self.main_app.carrier_list_pane is not None
            ):
                if hasattr(self.main_app.carrier_list_pane, "data_updated"):
                    self.main_app.carrier_list_pane.data_updated.connect(
                        self.main_app.retry_apply_date_range
                    )
            return

        # Second check: Carrier List validation
        if not os.path.exists("carrier_list.json"):
            CustomInfoDialog.information(
                self.main_app,
                "Carrier List Required",
                "The carrier list needs to be configured and saved before processing dates.\n\n"
                "1. Configure your carrier list\n"
                "2. Click 'Save/Apply' to save your changes",
            )

            # Automatically open carrier list pane
            self.main_app.carrier_list_button.setChecked(True)
            self.main_app.toggle_carrier_list_pane()

            if (
                hasattr(self.main_app, "carrier_list_pane")
                and self.main_app.carrier_list_pane is not None
            ):
                self.main_app.carrier_list_pane.data_updated.connect(
                    self.main_app.retry_apply_date_range
                )
            return

        # Third check: Carrier List content validation
        try:
            with open("carrier_list.json", "r", encoding="utf-8") as f:
                carrier_list = pd.DataFrame(json.load(f))
                if carrier_list.empty:
                    CustomInfoDialog.information(
                        self.main_app,
                        "Empty Carrier List",
                        "The carrier list is empty. Please add carriers before proceeding.",
                    )
                    self.main_app.carrier_list_button.setChecked(True)
                    self.main_app.toggle_carrier_list_pane()
                    return
        except (json.JSONDecodeError, pd.errors.EmptyDataError):
            CustomInfoDialog.information(
                self.main_app,
                "Invalid Carrier List",
                "The carrier list file is corrupted. Please reconfigure the carrier list.",
            )
            return
        except Exception as e:
            CustomInfoDialog.information(
                self.main_app,
                "Error",
                f"An unexpected error occurred while reading the carrier list: {str(e)}",
            )
            return

        # Create and show custom progress dialog
        progress = self.main_app.create_progress_dialog(
            "Processing Date Range", "Processing data..."
        )
        progress.show()

        def update_progress(value, message):
            progress.setValue(value)
            progress.setLabelText(message)
            QApplication.processEvents()
            return progress.was_canceled()

        try:
            # Initial setup (10%)
            if update_progress(0, "Initializing..."):
                return
            QApplication.processEvents()

            # Validate the date selection
            if (
                not hasattr(self.main_app, "date_selection_pane")
                or self.main_app.date_selection_pane is None
            ):
                raise AttributeError("Date selection pane is not initialized.")

            if (
                not hasattr(self.main_app.date_selection_pane, "selected_range")
                or self.main_app.date_selection_pane.selected_range is None
            ):
                raise ValueError("No date range selected.")

            # Get the selected date range
            start_date, end_date = self.main_app.date_selection_pane.selected_range
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Fetch clock ring data (20%)
            if update_progress(10, "Fetching clock ring data..."):
                return
            self.main_app.update_date_range_display(start_date_str, end_date_str)
            clock_ring_data = self.main_app.fetch_clock_ring_data(
                start_date_str, end_date_str
            )

            # Process carrier list (30%)
            if update_progress(20, "Processing carrier list..."):
                return
            try:
                with open("carrier_list.json", "r", encoding="utf-8") as json_file:
                    carrier_list = pd.DataFrame(json.load(json_file))

                # Ensure required columns exist in carrier_list
                required_columns = [
                    "carrier_name",
                    "list_status",
                    "route_s",
                    "hour_limit",
                    "effective_date",
                ]
                if not all(col in carrier_list.columns for col in required_columns):
                    raise ValueError(
                        f"Carrier list missing required columns: {required_columns}"
                    )

                # Normalize carrier_name for robust comparison
                carrier_list["carrier_name"] = (
                    carrier_list["carrier_name"].str.strip().str.lower()
                )
                clock_ring_data["carrier_name"] = (
                    clock_ring_data["carrier_name"].str.strip().str.lower()
                )

                # Drop existing list_status columns before merge if they exist
                columns_to_drop = ["list_status", "list_status_x", "list_status_y"]
                for col in columns_to_drop:
                    if col in clock_ring_data.columns:
                        clock_ring_data = clock_ring_data.drop(columns=[col])

                # Filter and merge clock ring data with all carrier list columns
                clock_ring_data = clock_ring_data[
                    clock_ring_data["carrier_name"].isin(carrier_list["carrier_name"])
                ]
                clock_ring_data = clock_ring_data.merge(
                    carrier_list, on="carrier_name", how="left"  # Merge all columns
                )

            except FileNotFoundError:
                CustomInfoDialog.information(
                    self.main_app,
                    "Missing Carrier List",
                    "Please configure and save the Carrier List before proceeding.",
                )
                return
            except Exception as e:
                print(f"Error processing carrier list: {str(e)}")
                clock_ring_data["list_status"] = "unknown"
                clock_ring_data["hour_limit"] = ""
                clock_ring_data["route_s"] = ""
                clock_ring_data["effective_date"] = ""
                CustomInfoDialog.information(
                    self.main_app,
                    "Warning",
                    f"Failed to process carrier list: {str(e)}\nProceeding with default values.",
                )

            # Clear existing data (35%)
            if update_progress(30, "Clearing existing data..."):
                return
            self.main_app.vio_85d_tab.refresh_data(pd.DataFrame())
            self.main_app.vio_85f_tab.refresh_data(pd.DataFrame())
            self.main_app.vio_85f_ns_tab.refresh_data(pd.DataFrame())
            self.main_app.vio_85f_5th_tab.refresh_data(pd.DataFrame())
            self.main_app.vio_85g_tab.refresh_data(pd.DataFrame())
            self.main_app.vio_MAX12_tab.refresh_data(pd.DataFrame())
            self.main_app.vio_MAX60_tab.refresh_data(pd.DataFrame())
            self.main_app.remedies_tab.refresh_data(pd.DataFrame())

            # Process violations (40-90%)
            if update_progress(40, "Processing violations..."):
                return
            self.update_violations_and_remedies(clock_ring_data, update_progress)

            # Update OTDL data (95%)
            if update_progress(95, "Updating OTDL data..."):
                return
            if self.main_app.otdl_maximization_pane is None:
                self.main_app.otdl_maximization_pane = OTDLMaximizationPane(
                    self.main_app
                )
            self.main_app.otdl_maximization_pane.refresh_data(
                clock_ring_data, clock_ring_data
            )

            # Complete (100%)
            update_progress(100, "Complete")
            self.main_app.statusBar().showMessage(
                "Date range processing complete", 5000
            )

        except ValueError as e:
            if str(e) == "No date range selected":
                progress.cancel()
                CustomInfoDialog.information(
                    self.main_app, "No Date Range", "Please select a date range first."
                )
            else:
                progress.cancel()
                CustomInfoDialog.information(
                    self.main_app, "Error", f"An unexpected error occurred: {str(e)}"
                )
        except Exception as e:
            progress.cancel()
            CustomInfoDialog.information(
                self.main_app, "Error", f"An unexpected error occurred: {str(e)}"
            )
        finally:
            self.main_app.cleanup_progress_dialog(progress)

    def update_otdl_violations(
        self, clock_ring_data, progress_callback=None, date_maximized_status=None
    ):
        """Update only OTDL-related violations (8.5.D and 8.5.G) and their tabs.

        Args:
            clock_ring_data: DataFrame containing clock ring data
            progress_callback: Function to update progress dialog
            date_maximized_status: Dictionary of maximization status changes from OTDL pane
        """
        if clock_ring_data is None or clock_ring_data.empty:
            return

        # Define OTDL-specific violation types
        violation_types = {
            "8.5.D": "8.5.D Overtime Off Route",
            "8.5.G": "8.5.G",
        }

        # Get unique dates and initialize maximization status if not provided
        unique_dates = (
            pd.to_datetime(clock_ring_data["rings_date"])
            .dt.strftime("%Y-%m-%d")
            .unique()
        )
        if date_maximized_status is None:
            date_maximized_status = {
                date: {"is_maximized": False} for date in unique_dates
            }

        # Calculate progress increments (40% for detection, 40% for tabs, 20% for summary)
        current_progress = 0

        try:
            # Detect violations (40% of progress)
            for key, violation_type in violation_types.items():
                if progress_callback:
                    if progress_callback(
                        current_progress, f"Processing {key} violations..."
                    ):
                        return

                self.violations[key] = detect_violations(
                    clock_ring_data, violation_type, date_maximized_status
                )
                current_progress += 20
                if progress_callback:
                    if progress_callback(
                        current_progress, f"Completed {key} violations"
                    ):
                        return

            # Update violation tabs (40% of progress)
            tab_updates = [
                (self.main_app.vio_85d_tab, "8.5.D", "8.5.D"),
                (self.main_app.vio_85g_tab, "8.5.G", "8.5.G"),
            ]

            for tab, key, description in tab_updates:
                if progress_callback:
                    if progress_callback(
                        current_progress, f"Updating {description} tab..."
                    ):
                        return
                tab.refresh_data(self.violations[key])
                current_progress += 20
                if progress_callback:
                    if progress_callback(
                        current_progress, f"Updated {description} tab"
                    ):
                        return

            # Update remedies (final 20%)
            if progress_callback:
                if progress_callback(80, "Updating violation summary..."):
                    return

            remedies_data = get_violation_remedies(clock_ring_data, self.violations)
            self.main_app.remedies_tab.refresh_data(remedies_data)

            if progress_callback:
                progress_callback(100, "OTDL maximization complete")

        except Exception as e:
            print(f"Error in update_otdl_violations: {str(e)}")
            raise

    def handle_maximized_status_change(self, date_str, changes):
        """Handle changes to OTDL maximization status"""
        if "8.5.D" not in self.violations and "8.5.G" not in self.violations:
            return

        # If it's not a batch update (old signal format), convert to batch format
        if not isinstance(changes, dict):
            changes = {
                date_str: {
                    "is_maximized": changes,
                    "excused_carriers": self.main_app.otdl_maximization_pane.get_excused_carriers(
                        date_str
                    ),
                }
            }

        # Create and show progress dialog immediately
        progress = CustomProgressDialog(
            "Processing OTDL Changes...",
            "Cancel",
            0,
            100,
            self.main_app,
            "OTDL Maximization",
        )
        progress.setWindowModality(Qt.ApplicationModal)
        progress.show()
        QApplication.processEvents()

        try:
            # Get the selected date range from the date selection pane
            if (
                not hasattr(self.main_app, "date_selection_pane")
                or self.main_app.date_selection_pane is None
                or not hasattr(self.main_app.date_selection_pane, "selected_range")
            ):
                raise ValueError("No date range selected")

            start_date, end_date = self.main_app.date_selection_pane.selected_range
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Load carrier list
            with open("carrier_list.json", "r", encoding="utf-8") as json_file:
                carrier_list = pd.DataFrame(json.load(json_file))

            # Fetch clock ring data
            clock_ring_data = self.main_app.fetch_clock_ring_data(
                start_date_str, end_date_str
            )
            if clock_ring_data.empty:
                return

            # Update carrier list data in clock ring data
            carrier_list["carrier_name"] = (
                carrier_list["carrier_name"].str.strip().str.lower()
            )
            clock_ring_data["carrier_name"] = (
                clock_ring_data["carrier_name"].str.strip().str.lower()
            )

            if "list_status" in clock_ring_data.columns:
                clock_ring_data = clock_ring_data.drop(columns=["list_status"])
            if "hour_limit" in clock_ring_data.columns:
                clock_ring_data = clock_ring_data.drop(columns=["hour_limit"])

            clock_ring_data = clock_ring_data.merge(
                carrier_list[["carrier_name", "list_status", "hour_limit"]],
                on="carrier_name",
                how="left",
            )

            # Update maximization status for the date range
            date_maximized_status = {}
            for d in pd.date_range(start_date_str, end_date_str):
                d_str = d.strftime("%Y-%m-%d")
                if d_str in changes:
                    date_maximized_status[d_str] = changes[d_str]
                else:
                    if hasattr(self.main_app.otdl_maximization_pane, "date_maximized"):
                        existing_status = (
                            self.main_app.otdl_maximization_pane.date_maximized.get(
                                d_str, {}
                            )
                        )
                        if isinstance(existing_status, dict):
                            date_maximized_status[d_str] = existing_status
                        else:
                            date_maximized_status[d_str] = {"is_maximized": False}

            # Create progress update function that uses our dialog
            def progress_update(value, message):
                progress.setValue(value)
                progress.setLabelText(message)
                QApplication.processEvents()
                return progress.was_canceled()

            # Use the optimized OTDL update function with maximization status
            self.update_otdl_violations(
                clock_ring_data, progress_update, date_maximized_status
            )

        except Exception as e:
            print(f"Error in handle_maximized_status_change: {str(e)}")
            traceback.print_exc()
        finally:
            self.main_app.cleanup_progress_dialog(progress)

    def update_violations_and_remedies(
        self, clock_ring_data=None, progress_callback=None
    ):
        """Helper function to detect violations and update all tabs."""
        if clock_ring_data is None or clock_ring_data.empty:
            return

        # Define violation types and their display names
        violation_types = {
            "8.5.D": "8.5.D Overtime Off Route",
            "8.5.F": "8.5.F Overtime Over 10 Hours Off Route",
            "8.5.F NS": "8.5.F NS Overtime On a Non-Scheduled Day",
            "8.5.F 5th": "8.5.F 5th More Than 4 Days of Overtime in a Week",
            "8.5.G": "8.5.G",
            "MAX12": "MAX12 More Than 12 Hours Worked in a Day",
            "MAX60": "MAX60 More Than 60 Hours Worked in a Week",
        }

        # Initialize violations dictionary
        self.violations = {}

        # Get unique dates from clock ring data and initialize date_maximized_status
        unique_dates = (
            pd.to_datetime(clock_ring_data["rings_date"])
            .dt.strftime("%Y-%m-%d")
            .unique()
        )
        date_maximized_status = {date: {"is_maximized": False} for date in unique_dates}

        # Calculate progress increments
        total_steps = len(violation_types) * 2  # Detection and tab updates
        progress_per_step = 90 / total_steps
        current_progress = 0

        try:
            # Detect violations (45% of progress)
            for key, violation_type in violation_types.items():
                if progress_callback:
                    if progress_callback(
                        int(current_progress), f"Processing {key} violations..."
                    ):
                        return  # Cancel if requested

                self.violations[key] = detect_violations(
                    clock_ring_data,
                    violation_type,
                    date_maximized_status if key in ["8.5.D", "8.5.G"] else None,
                )
                current_progress += progress_per_step
                if progress_callback:
                    if progress_callback(
                        int(current_progress), f"Completed {key} violations"
                    ):
                        return  # Cancel if requested

            # Update violation tabs (45% of progress)
            tab_updates = [
                (self.main_app.vio_85d_tab, "8.5.D", "8.5.D"),
                (self.main_app.vio_85f_tab, "8.5.F", "8.5.F"),
                (self.main_app.vio_85f_ns_tab, "8.5.F NS", "8.5.F NS"),
                (self.main_app.vio_85f_5th_tab, "8.5.F 5th", "8.5.F 5th"),
                (self.main_app.vio_85g_tab, "8.5.G", "8.5.G"),
                (self.main_app.vio_MAX12_tab, "MAX12", "MAX12"),
                (self.main_app.vio_MAX60_tab, "MAX60", "MAX60"),
            ]

            for tab, key, description in tab_updates:
                if progress_callback:
                    if progress_callback(
                        int(current_progress), f"Updating {description} tab..."
                    ):
                        return  # Cancel if requested
                tab.refresh_data(self.violations[key])
                current_progress += progress_per_step
                if progress_callback:
                    if progress_callback(
                        int(current_progress), f"Updated {description} tab"
                    ):
                        return  # Cancel if requested

            # Calculate and update remedies (final 10%)
            if progress_callback:
                if progress_callback(90, "Finalizing violation summary..."):
                    return  # Cancel if requested

            remedies_data = get_violation_remedies(clock_ring_data, self.violations)
            self.main_app.remedies_tab.refresh_data(remedies_data)

            if progress_callback:
                progress_callback(100, "OTDL maximization complete")

        except Exception as e:
            print(f"Error in update_violations_and_remedies: {str(e)}")
            raise
