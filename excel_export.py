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
from PyQt5.QtCore import (
    Qt,
    QTimer,
)
from PyQt5.QtGui import QColor

from custom_widgets import (
    CustomErrorDialog,
    CustomMessageBox,
    CustomProgressDialog,
    CustomWarningDialog,
)
from table_utils import extract_table_state
from theme import (
    COLOR_CELL_HIGHLIGHT,
    COLOR_WEEKLY_REMEDY,
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
        """Export all violation tabs to separate Excel files.

        Creates individual Excel files for each violation tab in the application,
        with proper formatting and data organization. Shows a progress dialog
        during the export process.

        The files are organized in folders by date range and include:
        - Formatted data with proper column types
        - Headers and footers
        - Consistent styling
        - Cell background colors
        - Column widths and alignments

        Raises:
            AttributeError: If required UI components are not initialized
            ValueError: If date selection is invalid
            Exception: For other export-related errors
        """
        try:
            # Get the selected date range
            date_range = self._get_date_range()

            # Setup folders
            base_folder_path = os.path.join(os.getcwd(), "spreadsheets")
            os.makedirs(base_folder_path, exist_ok=True)
            date_range_folder = os.path.join(base_folder_path, date_range)
            os.makedirs(date_range_folder, exist_ok=True)

            print(f"Exporting violations for date range: {date_range}")

            # Initialize export parameters
            self.tab_indices_to_process = list(
                range(self.main_window.central_tab_widget.count())
            )
            self.folder_path = date_range_folder
            self.date_range = date_range

            # Initialize the progress dialog
            self.progress_dialog = CustomProgressDialog(
                "Exporting tabs...",
                "Cancel",
                0,
                len(self.tab_indices_to_process),
                self.main_window,
                title="Export Progress",
            )
            self.progress_dialog.setWindowTitle("Export Progress")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)

            # Start processing tabs
            self.current_tab_index = 0
            self.timer = QTimer(self.main_window)
            self.timer.timeout.connect(self.process_next_tab_with_progress)
            self.timer.start(200)

        except (AttributeError, ValueError) as e:
            CustomErrorDialog.error(
                self.main_window, "Export Failed", f"Error: {str(e)}"
            )
            print(f"Export failed with error: {str(e)}")
        except Exception as e:
            print(f"Export failed with error: {e}")
            CustomErrorDialog.error(
                self.main_window, "Export Failed", f"An error occurred: {str(e)}"
            )

    def process_next_tab_with_progress(self):
        """Process the next tab in the export queue.

        Updates the progress dialog and handles the export of the current tab.
        Continues until all tabs are processed or the user cancels.

        Note:
            This method is called repeatedly by a timer to provide a responsive UI
            during the export process.
        """
        if self.progress_dialog.wasCanceled():
            self.timer.stop()
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

    def _get_date_range(self):
        """Get the selected date range for file naming.

        Returns:
            str: Date range in format "MM-DD-YYYY to MM-DD-YYYY"

        Raises:
            AttributeError: If date selection components are not initialized
            ValueError: If selected date is invalid or not a Saturday
        """
        if (
            not hasattr(self.main_window, "date_selection_pane")
            or self.main_window.date_selection_pane is None
        ):
            raise AttributeError(
                "Cannot Generate Spreadsheets Without Setting A Date First."
            )

        if (
            not hasattr(self.main_window.date_selection_pane, "calendar")
            or self.main_window.date_selection_pane.calendar is None
        ):
            raise AttributeError("Calendar widget is not initialized.")

        selected_date = self.main_window.date_selection_pane.calendar.selectedDate()
        if not selected_date.isValid():
            raise ValueError("No valid date selected in the calendar.")

        if selected_date.dayOfWeek() != 6:
            raise ValueError("Selected date must be a Saturday.")

        start_date = selected_date.toString("MM-dd-yyyy")
        end_date = selected_date.addDays(6).toString("MM-dd-yyyy")
        return f"{start_date} to {end_date}"

    def _write_excel_file(self, writer, date_range):
        """Write data to Excel with proper formatting.

        Creates worksheets with consistent styling including:
        - Headers with background colors
        - Proper column widths
        - Data type formatting
        - Borders and alignment
        - Title formatting

        Args:
            writer: Excel writer object
            date_range: Date range string for headers

        Note:
            Uses optimal text colors based on background colors for readability
        """
        workbook = writer.book
        border_color = "#424242"

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

        # Export each subtab (date-specific data) to its own worksheet
        if hasattr(current_tab, "date_tabs"):
            for i in range(current_tab.date_tabs.count()):
                subtab_name = current_tab.date_tabs.tabText(i)
                sanitized_sheet_name = self._sanitize_sheet_name(subtab_name)
                subtab_widget = current_tab.date_tabs.widget(i)

                # Extract table state with metadata
                content_df, metadata_df, row_highlights_df = extract_table_state(
                    subtab_widget
                )

                # If this is the 8.5.F 5th Summary tab, remove violation_dates
                if (
                    "violation_dates" in content_df.columns
                    and "8.5.F 5th" in subtab_name
                ):
                    # Remove the column from both content and metadata
                    content_df = content_df.drop(columns=["violation_dates"])
                    if metadata_df is not None:
                        metadata_df = metadata_df.drop(columns=["violation_dates"])

                # Write to Excel
                content_df.to_excel(
                    writer, sheet_name=sanitized_sheet_name, index=False, startrow=2
                )
                worksheet = writer.sheets[sanitized_sheet_name]

                # Add Title Header with or without Date Range
                if "Summary" in sanitized_sheet_name:
                    worksheet.merge_range(
                        0,
                        0,
                        0,
                        len(content_df.columns) - 1,
                        f"{current_tab_name} - {subtab_name} ({date_range})",
                        title_format,
                    )
                else:
                    worksheet.merge_range(
                        0,
                        0,
                        0,
                        len(content_df.columns) - 1,
                        f"{current_tab_name} - {subtab_name}",
                        title_format,
                    )

                # Write Column Headers
                for col_num, value in enumerate(content_df.columns):
                    worksheet.write(2, col_num, value, header_format)

                # Freeze the first 3 rows (title and headers)
                worksheet.freeze_panes(3, 0)  # Freeze 3 rows, 0 columns

                # Auto-Adjust Column Widths
                for col_num, col_name in enumerate(content_df.columns):
                    max_width = (
                        max(
                            content_df[col_name].astype(str).map(len).max(),
                            len(col_name),
                        )
                        + 2
                    )
                    worksheet.set_column(col_num, col_num, max_width)

                # Apply formatting with metadata
                for row_idx in range(len(content_df)):
                    for col_idx in range(len(content_df.columns)):
                        cell_value = content_df.iloc[row_idx, col_idx]
                        cell_meta = metadata_df.iloc[row_idx, col_idx]
                        row_highlight = row_highlights_df.iloc[row_idx]

                        format_props = {
                            "align": "center",
                            "border": 1,
                            "border_color": border_color,
                        }

                        # Get background color
                        if cell_meta["background"]:
                            bg_color = QColor(cell_meta["background"])
                        elif row_highlight:
                            bg_color = QColor(row_highlight)
                        else:
                            bg_color = QColor(45, 55, 60)  # Default background

                        # Calculate optimal text color for this background
                        text_color = calculate_optimal_gray(bg_color)

                        format_props["bg_color"] = bg_color.name()
                        format_props["font_color"] = text_color.name()

                        cell_format = workbook.add_format(format_props)
                        worksheet.write(row_idx + 3, col_idx, cell_value, cell_format)

    def _sanitize_sheet_name(self, sheet_name):
        """Sanitize the sheet name to be Excel-compatible.

        Args:
            sheet_name: The original sheet name

        Returns:
            str: A sanitized version of the sheet name that is valid for Excel

        Removes or replaces invalid characters and ensures the sheet name meets
        Excel's requirements.
        """
        invalid_chars = r"[]:*?/\\"
        for char in invalid_chars:
            sheet_name = sheet_name.replace(char, "_")
        return sheet_name[:31]  # Excel limits sheet names to 31 characters

    # ... (continue with other helper methods like _write_excel_file)
