"""Module for exporting violation data to Excel format.

This module provides functionality to export violation data and summaries
to Excel workbooks, with features including:
- Customizable worksheet formatting
- Data filtering and organization
- Summary statistics
- Multi-sheet workbooks for different violation types
"""

import os

import pandas as pd
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QTableView,
)

from custom_widgets import (
    CustomErrorDialog,
    CustomMessageBox,
    CustomWarningDialog,
)
from table_utils import extract_table_state
from theme import (
    COLOR_CELL_HIGHLIGHT,
    COLOR_TEXT_LIGHT,
    COLOR_WEEKLY_REMEDY,
    MATERIAL_GREY_800,
    MATERIAL_SURFACE,
)
from violation_model import calculate_optimal_gray


class ExcelExporter:
    """Handles the export of application data to Excel format.

    Provides functionality for converting and exporting various types of application
    data (violations, carrier information, etc.) to Excel spreadsheet format.
    Includes progress tracking and error handling.

    Attributes:
        main_window: Reference to main application window
        progress_dialog: Dialog showing export progress
        timer: Timer for processing tabs
        current_tab_index: Index of tab being processed
        tab_indices_to_process: List of tab indices to export
        folder_path: Path where Excel files will be saved
        date_range: Date range string for file naming
    """

    def __init__(self, main_window):
        """Initialize the Excel exporter.

        Args:
            main_window: Reference to the main application window
        """
        self.main_window = main_window
        self.progress_dialog = None
        self.timer = None
        self.current_tab_index = 0
        self.tab_indices_to_process = []
        self.folder_path = None
        self.date_range = None

    def export_all_violations(self):
        """Export all violation tabs to Excel files."""
        try:
            # Get the current date range
            self.date_range = self._get_date_range()

            # Setup folders
            base_folder_path = os.path.join(os.getcwd(), "spreadsheets")
            os.makedirs(base_folder_path, exist_ok=True)
            self.folder_path = os.path.join(base_folder_path, self.date_range)
            os.makedirs(self.folder_path, exist_ok=True)

            # Initialize export parameters
            self.tab_indices_to_process = list(
                range(self.main_window.central_tab_widget.count())
            )

            # Create progress dialog
            self.progress_dialog = self.main_window.create_progress_dialog(
                "Exporting Violations", "Preparing to export..."
            )
            self.progress_dialog.setRange(0, len(self.tab_indices_to_process))
            self.progress_dialog.show()

            # Start the export process
            self.current_tab_index = 0
            self.timer = QTimer()
            self.timer.timeout.connect(self.process_next_tab_with_progress)
            self.timer.start(100)  # Process a tab every 100ms

        except (AttributeError, ValueError) as e:
            CustomErrorDialog.error(
                self.main_window, "Export Failed", f"Error: {str(e)}"
            )
        except Exception as e:
            CustomErrorDialog.error(
                self.main_window,
                "Export Failed",
                f"An unexpected error occurred: {str(e)}",
            )

    def process_next_tab_with_progress(self):
        """Process the next tab in the export queue."""
        if self.progress_dialog.wasCanceled():
            self.timer.stop()
            self.main_window.cleanup_progress_dialog(self.progress_dialog)
            CustomWarningDialog.warning(
                self.main_window, "Export Canceled", "The export process was canceled."
            )
            return

        if self.current_tab_index < len(self.tab_indices_to_process):
            tab_index = self.tab_indices_to_process[self.current_tab_index]
            self.main_window.central_tab_widget.setCurrentIndex(tab_index)
            current_tab_name = self.main_window.central_tab_widget.tabText(tab_index)

            print(f"Processing tab: {current_tab_name}")

            sanitized_tab_name = current_tab_name.replace(" ", "_").replace("/", "_")
            file_name = f"{sanitized_tab_name} - {self.date_range}.xlsx"
            file_path = os.path.join(self.folder_path, file_name)

            try:
                self.export_to_excel_custom_path(file_path)
                print(f"Exported '{current_tab_name}' to file: {file_path}")
            except Exception as e:
                print(f"Failed to export '{current_tab_name}': {e}")

            self.current_tab_index += 1
            self.progress_dialog.setValue(self.current_tab_index)
            self.progress_dialog.setLabelText(f"Exporting tab: {current_tab_name}")
        else:
            self.timer.stop()
            self.progress_dialog.setValue(len(self.tab_indices_to_process))
            self.main_window.cleanup_progress_dialog(self.progress_dialog)

            # Use custom message box instead of QMessageBox
            msg_box = CustomMessageBox(
                "Export Successful",
                f"All violation tabs have been exported to '{self.folder_path}'.",
                self.main_window,
            )
            msg_box.show()

            # Open the folder in File Explorer
            try:
                os.startfile(self.folder_path)
            except Exception as e:
                print(f"Failed to open folder: {e}")

    def export_to_excel_custom_path(self, save_path):
        """Export the current tab to a specific Excel file path.

        Args:
            save_path (str): Full path where the Excel file should be saved

        Raises:
            Exception: If export fails for any reason
        """
        try:
            date_range = self._get_date_range()
            with pd.ExcelWriter(save_path, engine="xlsxwriter") as writer:
                self._write_excel_file(writer, date_range)

            current_tab_name = self.main_window.central_tab_widget.tabText(
                self.main_window.central_tab_widget.currentIndex()
            )
            print(f"Exported '{current_tab_name}' successfully.")

        except Exception as e:
            print(f"Export failed with error: {e}")
            raise

    def get_date_range(self):
        """Get the currently selected date range.

        Returns:
            tuple: (start_date, end_date) as strings in YYYY-MM-DD format,
                   or (None, None) if no valid range selected
        """
        try:
            if (
                not hasattr(self.main_window, "date_selection_pane")
                or self.main_window.date_selection_pane is None
                or not hasattr(self.main_window.date_selection_pane, "selected_range")
                or self.main_window.date_selection_pane.selected_range is None
            ):
                return None, None

            start_date, end_date = self.main_window.date_selection_pane.selected_range
            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

        except Exception as e:
            print(f"Error getting date range: {e}")
            return None, None

    def _write_excel_file(self, writer, date_range):
        """Write data to Excel with proper formatting."""
        workbook = writer.book
        border_color = MATERIAL_GREY_800.name().lstrip("#")

        # Calculate optimal text colors for our header backgrounds
        header_bg = COLOR_CELL_HIGHLIGHT
        title_bg = COLOR_WEEKLY_REMEDY
        header_text_color = calculate_optimal_gray(header_bg)
        title_text_color = calculate_optimal_gray(title_bg)

        # Update formats to use calculated text colors
        header_format = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "bg_color": header_bg.name(),
                "font_color": header_text_color.name(),
                "border": 1,
                "border_color": border_color,
            }
        )

        title_format = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "font_size": 14,
                "bg_color": title_bg.name(),
                "font_color": title_text_color.name(),
                "border": 1,
                "border_color": border_color,
            }
        )

        # Get the currently active tab
        current_tab_index = self.main_window.central_tab_widget.currentIndex()
        current_tab = self.main_window.central_tab_widget.widget(current_tab_index)
        current_tab_name = self.main_window.central_tab_widget.tabText(
            current_tab_index
        )

        # Keep track of used worksheet names to avoid duplicates
        used_worksheet_names = set()

        # Process each subtab
        for subtab_idx in range(current_tab.date_tabs.count()):
            # Update progress through main GUI
            QApplication.processEvents()  # Allow GUI to update

            subtab_name = current_tab.date_tabs.tabText(subtab_idx)

            # Initialize model as None
            model = None
            table_view = None

            # Get table view - handle Summary tab specially
            if subtab_name == "Summary":
                if hasattr(current_tab, "summary_proxy_model"):
                    model = current_tab.summary_proxy_model
                    table_view = current_tab.date_tabs.widget(subtab_idx).findChild(
                        QTableView
                    )
                else:
                    continue
            else:
                # Get table view from the models dictionary
                if hasattr(current_tab, "models") and subtab_name in current_tab.models:
                    model_info = current_tab.models[subtab_name]
                    table_view = model_info["tab"].findChild(QTableView)
                else:
                    continue

            if not table_view:
                print(f"No table view found for tab: {subtab_name}")
                continue

            if not model:
                model = table_view.model()
            if not model:
                continue

            # Extract table state using the utility function that handles proxy models
            content_df, metadata_df, _ = extract_table_state(table_view)

            # Sort by carrier name for Excel export
            if (
                content_df is not None
                and not content_df.empty
                and "Carrier Name" in content_df.columns
            ):
                content_df = content_df.sort_values("Carrier Name", ascending=True)
                # Reset index to ensure we write rows in sorted order
                content_df = content_df.reset_index(drop=True)
                # Reorder metadata to match the sorted content
                metadata_df = metadata_df.reindex(content_df.index)

            if content_df is None or content_df.empty:
                continue

            # Create worksheet name to match GUI exactly
            if subtab_name == "Summary":
                worksheet_name = "Summary"
            else:
                worksheet_name = subtab_name  # Use the exact subtab name from the GUI

            # Ensure unique worksheet name if needed
            base_worksheet_name = worksheet_name
            counter = 1
            while worksheet_name.lower() in used_worksheet_names:
                # If name exists, add a number suffix
                suffix = f" ({counter})"
                # Calculate available space for the base name
                available_space = 31 - len(suffix)
                worksheet_name = f"{base_worksheet_name[:available_space]}{suffix}"
                counter += 1

            used_worksheet_names.add(worksheet_name.lower())
            worksheet = workbook.add_worksheet(worksheet_name)

            # Write title
            title = f"{current_tab_name} - {date_range}"
            worksheet.merge_range(
                0, 0, 0, len(content_df.columns) - 1, title, title_format
            )

            # Write headers
            for col, header in enumerate(content_df.columns):
                worksheet.write(1, col, header, header_format)

            # Write data with formatting - using DataFrame's order
            for row_idx, row in enumerate(range(len(content_df))):
                for col in range(len(content_df.columns)):
                    cell_format = workbook.add_format(
                        {
                            "bg_color": MATERIAL_SURFACE.name().lstrip("#"),
                            "border": 1,
                            "border_color": border_color,
                        }
                    )
                    cell_format.set_font_color(COLOR_TEXT_LIGHT.name().lstrip("#"))

                    # Get cell metadata
                    cell_metadata = metadata_df.iloc[row, col]

                    # Apply background color if present
                    bg_color = cell_metadata.get("background")
                    if bg_color:
                        cell_format.set_bg_color(bg_color)

                    # Always apply the foreground color from metadata
                    text_color = cell_metadata.get("foreground")
                    if text_color:
                        cell_format.set_font_color(text_color)
                    else:
                        # Default to white text on dark background for better visibility
                        cell_format.set_font_color("#FFFFFF")

                    value = content_df.iloc[row, col]
                    worksheet.write(row_idx + 2, col, value, cell_format)

            # Auto-fit columns based on content and GUI widths
            for _, col in enumerate(range(len(content_df.columns))):
                # Get the column width from the GUI if available
                gui_width = table_view.columnWidth(col)
                excel_width = (
                    gui_width / 7
                )  # Convert pixels to Excel units (approximate)

                # Calculate width based on content
                header_length = len(str(content_df.columns[col]))
                content_lengths = [
                    len(str(content_df.iloc[row, col]))
                    for row in range(len(content_df))
                ]
                max_content_length = max(content_lengths) if content_lengths else 0
                content_width = max(header_length, max_content_length)

                # Use the larger of GUI width or content width, with some padding
                final_width = max(excel_width, content_width + 2)

                # Ensure minimum width of 8 and maximum of 50
                final_width = max(8, min(50, final_width))

                worksheet.set_column(col, col, final_width)

            # Freeze panes
            worksheet.freeze_panes(2, 0)

    def _sanitize_sheet_name(self, sheet_name):
        """Sanitize the sheet name to be Excel-compatible.

        Args:
            sheet_name: The original sheet name

        Returns:
            str: A sanitized version of the sheet name that is valid for Excel

        Removes or replaces invalid characters and ensures the sheet name meets
        Excel's requirements.
        """
        # First replace invalid characters
        invalid_chars = r"[]:*?/\\"
        for char in invalid_chars:
            sheet_name = sheet_name.replace(char, "_")

        # If the name is too long, try to preserve both parts
        if len(sheet_name) > 31:
            parts = sheet_name.split(" - ")
            if len(parts) == 2:
                tab_name, date = parts
                # Try to keep both parts by shortening the first part
                available_space = 31 - len(date) - 3  # 3 for " - "
                if (
                    available_space > 10
                ):  # Only if we can keep a reasonable part of the tab name
                    return f"{tab_name[:available_space]} - {date}"

            # If we can't preserve both parts nicely, just truncate
            return sheet_name[:31]

        return sheet_name

    def _get_date_range(self):
        """Get the current date range from the main window.

        Returns:
            str: Date range in format 'YYYY-MM-DD to YYYY-MM-DD'

        Raises:
            AttributeError: If date selection pane is not initialized
            ValueError: If no valid date is selected
        """
        if (
            not hasattr(self.main_window, "date_selection_pane")
            or self.main_window.date_selection_pane is None
            or not hasattr(self.main_window.date_selection_pane, "selected_range")
            or self.main_window.date_selection_pane.selected_range is None
        ):
            raise AttributeError("No valid date range selected")

        start_date, end_date = self.main_window.date_selection_pane.selected_range
        return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

    # ... (continue with other helper methods like _write_excel_file)
