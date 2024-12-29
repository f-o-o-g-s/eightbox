"""Manager class for handling moves cleaning functionality.

This module provides a centralized manager for:
1. Showing the clean moves dialog
2. Handling cleaned moves data
3. Coordinating between the UI and database operations
"""

import json

import pandas as pd
from PyQt5.QtCore import (
    QObject,
    Qt,
)
from PyQt5.QtWidgets import QApplication

from clean_moves.ui.clean_moves_dialog import CleanMovesDialog
from clean_moves.utils.clean_moves_utils import (
    detect_invalid_moves,
    get_valid_routes,
)
from custom_widgets import (
    CustomInfoDialog,
    CustomProgressDialog,
    CustomWarningDialog,
)


class MovesManager(QObject):
    """Manager class for handling moves cleaning functionality."""

    def __init__(self, main_app):
        """Initialize the moves manager.

        Args:
            main_app: Reference to the main application window
        """
        super().__init__()
        self.main_app = main_app
        self.active_progress_dialogs = []

    def show_clean_moves_dialog(self):
        """Show the Clean Moves dialog.

        Detects moves entries with invalid route numbers and allows
        the user to clean them. Only shows entries for WAL and NL carriers
        from the carrier list.
        """
        # Get current data from the date range
        current_data = self.main_app.fetch_clock_ring_data()

        if current_data.empty:
            CustomWarningDialog.warning(
                self.main_app, "No Data", "Please select a date range first."
            )
            return

        # Get valid routes
        valid_routes = get_valid_routes(self.main_app.eightbox_db_path)
        if not valid_routes:
            CustomWarningDialog.warning(
                self.main_app,
                "Error",
                "Failed to get valid route numbers from database.",
            )
            return

        # Load carrier list
        try:
            with open("carrier_list.json", "r", encoding="utf-8") as f:
                carrier_list = json.load(f)
                # Only include WAL and NL carriers
                valid_carriers = {
                    carrier["carrier_name"].lower()
                    for carrier in carrier_list
                    if carrier["list_status"].lower() in ["wal", "nl"]
                }
        except Exception as e:
            CustomWarningDialog.warning(
                self.main_app, "Error", f"Failed to load carrier list: {str(e)}"
            )
            return

        # Detect invalid moves
        invalid_moves = detect_invalid_moves(
            current_data, self.main_app.eightbox_db_path
        )
        if invalid_moves.empty:
            CustomInfoDialog.information(
                self.main_app,
                "No Invalid Moves",
                "No moves entries with invalid route numbers were found.",
            )
            return

        # Filter invalid moves to only include WAL and NL carriers from the carrier list
        invalid_moves = invalid_moves[
            invalid_moves["carrier_name"].str.lower().isin(valid_carriers)
        ]

        if invalid_moves.empty:
            CustomInfoDialog.information(
                self.main_app,
                "No Invalid Moves",
                "No moves entries with invalid route numbers were found for WAL and NL carriers.",
            )
            return

        # Create and show dialog
        dialog = CleanMovesDialog(invalid_moves, valid_routes, self.main_app)
        dialog.moves_cleaned.connect(
            lambda cleaned: self.handle_cleaned_moves(cleaned, current_data)
        )
        dialog.exec_()

    def handle_cleaned_moves(self, cleaned_moves, current_data):
        """Handle cleaned moves data from the dialog.

        Args:
            cleaned_moves: Dictionary mapping (carrier, date) to cleaned moves string
            current_data: The current DataFrame of clock ring data
        """
        if not cleaned_moves:
            return

        # Create progress dialog
        progress = self.create_progress_dialog(
            "Updating Moves", "Applying cleaned moves data..."
        )
        progress.show()

        try:
            # Phase 1: Update moves (0-30%)
            progress.setLabelText("Updating moves data...")
            progress.setValue(10)
            QApplication.processEvents()

            for (carrier, date), moves in cleaned_moves.items():
                mask = (current_data["carrier_name"] == carrier) & (
                    current_data["rings_date"] == date
                )
                current_data.loc[mask, "moves"] = moves

            progress.setValue(30)
            QApplication.processEvents()

            # Phase 1.5: Merge carrier list data (30-50%)
            progress.setLabelText("Updating carrier data...")
            progress.setValue(40)
            QApplication.processEvents()

            try:
                with open("carrier_list.json", "r", encoding="utf-8") as json_file:
                    carrier_list = pd.DataFrame(json.load(json_file))

                # Normalize carrier names
                carrier_list["carrier_name"] = (
                    carrier_list["carrier_name"].str.strip().str.lower()
                )
                current_data["carrier_name"] = (
                    current_data["carrier_name"].str.strip().str.lower()
                )

                # Drop existing list_status and hour_limit columns if they exist
                columns_to_drop = [
                    "list_status",
                    "list_status_x",
                    "list_status_y",
                    "hour_limit",
                ]
                for col in columns_to_drop:
                    if col in current_data.columns:
                        current_data = current_data.drop(columns=[col])

                # Merge with carrier list data
                current_data = current_data.merge(
                    carrier_list[["carrier_name", "list_status", "hour_limit"]],
                    on="carrier_name",
                    how="left",
                )

            except Exception as e:
                print(f"Error merging carrier list data: {e}")
                current_data["list_status"] = "unknown"
                current_data["hour_limit"] = 12.00

            progress.setValue(50)
            QApplication.processEvents()

            # Phase 2: Reprocess violations (50-90%)
            progress.setLabelText("Reprocessing violations...")
            progress.setValue(60)
            QApplication.processEvents()

            self.main_app.update_violations_and_remedies(current_data)

            progress.setValue(90)
            QApplication.processEvents()

            # Phase 3: Cleanup (90-100%)
            progress.setLabelText("Finalizing changes...")
            progress.setValue(100)
            QApplication.processEvents()

        except Exception as e:
            # Clean up progress dialog before showing error
            self.cleanup_progress_dialog(progress)
            CustomWarningDialog.warning(
                self.main_app, "Error", f"Failed to process cleaned moves: {str(e)}"
            )
            return

        # Clean up progress dialog before showing success
        self.cleanup_progress_dialog(progress)

        # Show success message after progress dialog is cleaned up
        CustomInfoDialog.information(
            self.main_app,
            "Success",
            "Moves data has been cleaned and violations reprocessed.",
        )

    def create_progress_dialog(self, title="Processing...", initial_text=""):
        """Create and track a new progress dialog.

        Args:
            title (str): Title for the progress dialog
            initial_text (str): Initial message to display

        Returns:
            CustomProgressDialog: The created progress dialog
        """
        progress = CustomProgressDialog(
            initial_text, "Cancel", 0, 100, self.main_app, title=title
        )
        progress.setWindowModality(Qt.WindowModal)
        self.active_progress_dialogs.append(progress)
        return progress

    def cleanup_progress_dialog(self, progress):
        """Clean up and close a progress dialog.

        Args:
            progress (CustomProgressDialog): The progress dialog to clean up
        """
        if progress in self.active_progress_dialogs:
            self.active_progress_dialogs.remove(progress)
        progress.close()
