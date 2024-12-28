"""Manager for cleaning invalid moves data.

This module provides a manager class that:
1. Shows the clean moves dialog
2. Handles cleaned moves updates
3. Coordinates between UI and data operations
"""

import json
from typing import Dict

from PyQt5.QtWidgets import QApplication

from clean_moves_dialog import CleanMovesDialog
from clean_moves_utils import (
    detect_invalid_moves,
    get_valid_routes,
)
from custom_widgets import (
    CustomInfoDialog,
    CustomWarningDialog,
)


class CleanMovesManager:
    """Manager for cleaning invalid moves data."""

    def __init__(self, main_app):
        """Initialize the manager.

        Args:
            main_app: Reference to the main application instance
        """
        self.main_app = main_app

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

    def handle_cleaned_moves(self, cleaned_moves: Dict[tuple, str], current_data):
        """Handle cleaned moves data from the dialog.

        Args:
            cleaned_moves: Dictionary mapping (carrier, date) to cleaned moves string
            current_data: The current DataFrame of clock ring data
        """
        if not cleaned_moves:
            return

        # Create progress dialog
        progress = self.main_app.create_progress_dialog(
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

            # Update the main app's current data
            self.main_app.current_data = current_data

            # Update all tabs
            self.main_app.update_all_tabs()

            # Show success message
            CustomInfoDialog.information(
                self.main_app,
                "Success",
                "Moves data has been updated successfully.",
            )

        except Exception as e:
            CustomWarningDialog.warning(
                self.main_app, "Error", f"Failed to update moves: {str(e)}"
            )

        finally:
            progress.close()
