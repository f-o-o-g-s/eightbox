"""Data model and display logic for USPS carrier overtime violations.

This module provides the data model and display functionality for tracking and
visualizing USPS carrier overtime violations, including:

- Article 8.5.D violations (overtime off assignment)
- Article 8.5.F violations (over 10 hours, non-scheduled day, and 5th day)
- Maximum work hour violations (12-hour daily and 60-hour weekly limits)

Key features:
- Dynamic color coding for violations and remedies
- Automatic contrast calculations for text readability
- Filtering and sorting capabilities
- Weekly and daily hour tracking
- Specialized handling for different carrier types (OTDL, WAL, NL, PTF)

The module serves as the presentation layer for violation data, handling both
the data model and visual formatting for the violation tracking interface.
"""

import pandas as pd
from PyQt5.QtCore import (
    QSortFilterProxyModel,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QStandardItem,
    QStandardItemModel,
)

from violation_types import ViolationType

# We can remove the theme import entirely since we're calculating all text colors dynamically

# fully opaque
VIOLATION_COLOR = QColor(125, 89, 168)  # Medium dark purple (7D59A8)
# Softer background for summary rows with violations
SUMMARY_ROW_COLOR = QColor(
    215, 183, 255
)  # D7B7FF is a lighter shade of purple/lavender
# Teal color for positive weekly totals
WEEKLY_TOTAL_COLOR = QColor(2, 145, 132)  # Teal color for weekly remedy totals


def calculate_optimal_gray(bg_color, target_ratio=7.0):
    """Calculate optimal gray value for given background color"""
    bg_luminance = (
        0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
    ) / 255

    # Binary search for optimal gray value
    left, right = 0, 255
    best_gray = 0
    best_diff = float("inf")

    while left <= right:
        gray = (left + right) // 2
        gray_luminance = gray / 255

        # Calculate contrast ratio
        lighter = max(gray_luminance, bg_luminance) + 0.05
        darker = min(gray_luminance, bg_luminance) + 0.05
        ratio = lighter / darker

        diff = abs(ratio - target_ratio)
        if diff < best_diff:
            best_diff = diff
            best_gray = gray

        if ratio < target_ratio:
            # For dark backgrounds, prefer lighter text
            if bg_luminance < 0.5:
                left = gray + 1
            # For light backgrounds, prefer darker text
            else:
                right = gray - 1
        else:
            if bg_luminance < 0.5:
                right = gray - 1
            else:
                left = gray + 1

    return QColor(best_gray, best_gray, best_gray)


class ViolationModel(QStandardItemModel):
    """Qt data model for displaying and formatting violation data.

    Handles the interface between pandas DataFrames and Qt's model/view architecture.
    Provides functionality for:
    - Data display and formatting
    - Dynamic color coding for violations
    - Automatic text contrast calculation
    - Custom sorting behavior
    - Cell metadata tracking

    Attributes:
        df (pd.DataFrame): The violation data being displayed
        tab_type (ViolationType): The type of violation being displayed
        is_summary (bool): Whether this is a summary view
    """

    def __init__(self, data, tab_type: ViolationType = None, is_summary=False):
        super().__init__()
        self.df = data
        self.tab_type = tab_type
        self.is_summary = is_summary
        self.setup_model()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.BackgroundRole:
            return self.get_background_color(index)
        elif role == Qt.ForegroundRole:
            return self.get_foreground_color(index)
        elif role == Qt.DisplayRole:
            return self.get_display_value(index)
        elif role == Qt.UserRole:  # Use UserRole for sorting
            value = self.item(index.row(), index.column()).text()
            try:
                # Try to extract numeric part for sorting
                parts = value.split()
                if parts and any(char.isdigit() for char in parts[0]):
                    return float(parts[0])
                # If no numeric part, sort by the full string
                return value
            except (ValueError, TypeError):
                return value

        return super().data(index, role)

    def get_background_color(self, index):
        """Get background color based on violation type and tab type.

        Determines cell background colors based on:
        - Violation type (8.5.D, 8.5.F, Max12, Max60, etc.)
        - Whether it's a summary or daily tab
        - Column type (remedy total, weekly total, etc.)
        - Cell value (violation thresholds)
        - Carrier list status (for certain violations)

        Args:
            index (QModelIndex): The cell index

        Returns:
            QColor: Background color for the cell, or None for default
        """
        row = index.row()
        col = index.column()
        col_name = self.headerData(col, Qt.Horizontal, Qt.DisplayRole)
        value = self.data(index, Qt.DisplayRole)

        # Start with row-level highlighting for violations
        background_color = SUMMARY_ROW_COLOR if self.has_violation_in_row(row) else None

        # Add ViolationRemedies tab type handling
        # (Violations Summary BIG PARENT tab)
        if self.tab_type == ViolationType.VIOLATION_REMEDIES:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # All other numeric columns in purple when > 0
                elif col_name not in ["carrier_name", "list_status"]:
                    try:
                        number = float(str(value))
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError):
                        pass
            else:
                # Daily tab formatting
                if col_name == "Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR  # Using teal for Remedy Total
                    except (ValueError, TypeError, IndexError):
                        pass
                # All other numeric columns in purple when > 0
                elif col_name not in ["carrier_name", "list_status"]:
                    try:
                        number = float(str(value))
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError):
                        pass

        # Then apply specific cell colors that should override the row highlight
        elif self.tab_type == ViolationType.EIGHT_FIVE_D:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # Individual day columns in darker purple when > 0
                elif col_name not in [
                    "Carrier Name",
                    "List Status",
                ]:  # Skip non-numeric columns
                    try:
                        number = float(str(value))
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError):
                        pass
            else:
                # Daily tab formatting
                if col_name == "Remedy Total" and value:
                    try:
                        if float(str(value)) > 0:
                            return VIOLATION_COLOR
                    except ValueError:
                        pass

        elif self.tab_type == ViolationType.EIGHT_FIVE_F:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # Check if current date column exists in the violation_dates
                # for this specific row
                elif col_name not in ["Carrier Name", "List Status", "violation_dates"]:
                    try:
                        # Get the violation dates for this row
                        violation_dates_col = self.df.columns.get_loc("violation_dates")
                        violation_dates = self.data(
                            self.index(row, violation_dates_col), Qt.DisplayRole
                        )
                        if violation_dates and col_name in str(violation_dates):
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, KeyError):
                        pass
            else:
                # Daily tab formatting - same as other violation types
                if col_name == "Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass

        elif self.tab_type == ViolationType.EIGHT_FIVE_F_5TH:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # Check if current date column exists in the violation_dates
                # for this specific row
                elif col_name not in ["Carrier Name", "List Status", "violation_dates"]:
                    try:
                        # Get the violation dates for this row
                        violation_dates_col = self.df.columns.get_loc("violation_dates")
                        violation_dates = self.data(
                            self.index(row, violation_dates_col), Qt.DisplayRole
                        )
                        if violation_dates and col_name in str(violation_dates):
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, KeyError):
                        pass
            else:
                # Daily tab formatting - same as other violation types
                if col_name == "Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass

        elif self.tab_type == ViolationType.EIGHT_FIVE_F_NS:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # Individual day columns in darker purple when > 0
                elif col_name not in [
                    "Carrier Name",
                    "List Status",
                ]:  # Skip non-numeric columns
                    try:
                        number = float(str(value))
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError):
                        pass
            else:
                # Daily tab formatting
                if col_name == "Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass

        elif self.tab_type == ViolationType.MAX_12:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # Check daily hours against carrier type limit
                elif col_name not in ["Carrier Name", "List Status"]:
                    try:
                        # Get list_status for this row
                        list_status_col = next(
                            i
                            for i, col in enumerate(self.df.columns)
                            if col in ["List Status", "list_status"]
                        )
                        list_status = str(
                            self.data(self.index(row, list_status_col), Qt.DisplayRole)
                        ).lower()

                        # Set hour limit based on list_status
                        hour_limit = 12.00 if list_status == "otdl" else 11.50

                        # Check if hours exceed limit
                        number = float(str(value))
                        if number > hour_limit:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
            else:
                # Daily tab formatting - same as other violation types
                if col_name == "Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass

        elif self.tab_type == ViolationType.MAX_60:
            if self.is_summary:
                # Weekly Remedy Total in teal
                if col_name == "Weekly Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return WEEKLY_TOTAL_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass
                # Highlight Cumulative Hours > 60 in darker purple (except for PTF)
                elif col_name == "Cumulative Hours":
                    try:
                        # Find list status column by checking headers
                        list_status_col = None
                        for i in range(self.columnCount()):
                            header = self.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                            if header in ["List Status", "list_status"]:
                                list_status_col = i
                                break

                        if list_status_col is not None:
                            list_status = str(
                                self.data(
                                    self.index(row, list_status_col), Qt.DisplayRole
                                )
                            ).lower()

                            # Only highlight if not PTF and hours > 60
                            if list_status != "ptf":
                                number = float(str(value))
                                if number > 60:
                                    return VIOLATION_COLOR
                    except (ValueError, TypeError):
                        pass
            else:
                # Daily tab formatting - same as other violation types
                if col_name == "Remedy Total":
                    try:
                        number = float(str(value).split()[0])
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError, IndexError):
                        pass

        return background_color

    def has_violation_in_row(self, row):
        """Check if the row contains any violations."""
        for col in range(self.columnCount()):
            header = self.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            if header in ["violation_type", "Violation Type"]:
                value = self.data(self.index(row, col), Qt.DisplayRole)
                # Check for both types of non-violation messages
                return not (value.startswith("No Violation"))
            elif header in ["Weekly Remedy Total", "Remedy Total"]:
                value = self.data(self.index(row, col), Qt.DisplayRole)
                try:
                    return float(str(value).replace(",", "")) > 0.00
                except (ValueError, TypeError):
                    continue
        return False

    def get_foreground_color(self, index):
        """Get text color based on background color for contrast."""
        background_color = self.get_background_color(index)

        if background_color is None:
            # Use white text on dark theme (assuming dark theme background)
            return calculate_optimal_gray(
                QColor(18, 18, 18)  # #121212 (MATERIAL_BACKGROUND)
            )

        # Handle QBrush objects
        if isinstance(background_color, QBrush):
            background_color = background_color.color()

        return calculate_optimal_gray(background_color)

    def get_display_value(self, index):
        """Get the display value for the cell."""
        value = self.item(index.row(), index.column()).text()

        # Try to convert to float and format if successful
        try:
            # Check if the value is a string containing a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                # Handle strings like "8.00 (NS day)" by splitting and formatting just the number
                parts = value.split()
                if parts:
                    try:
                        number = float(parts[0])
                        formatted_number = f"{number:.2f}"
                        # If there were additional parts (like "(NS day)"), add them back
                        if len(parts) > 1:
                            return f"{formatted_number} {' '.join(parts[1:])}"
                        return formatted_number
                    except ValueError:
                        pass

            # Handle pure numerical values
            number = float(value)
            return f"{number:.2f}"
        except (ValueError, TypeError):
            # If conversion fails, return the original value
            return value

    def setup_model(self):
        """Setup the model with data."""
        # Clear any existing data
        self.clear()

        # Set headers using DataFrame columns
        self.setHorizontalHeaderLabels(list(map(str, self.df.columns)))

        # Populate data
        for row in range(len(self.df)):
            for col in range(len(self.df.columns)):
                value = self.df.iloc[row, col]
                item = QStandardItem(str(value))
                self.setItem(row, col, item)

    def get_violation_column(self):
        """Get the index of the violation_type column."""
        try:
            return self.df.columns.get_loc("violation_type")
        except KeyError:
            # If violation_type column doesn't exist, return carrier_name column (0)
            return 0

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Override headerData to display the column names from the DataFrame."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self.df.columns):
                return str(self.df.columns[section])
        return super().headerData(section, orientation, role)

    def get_cell_metadata(self, index):
        """Get metadata for a specific cell including background and text colors."""
        if not index.isValid():
            return None

        metadata = {
            "value": self.data(index, Qt.DisplayRole),
            "background": None,
            "text_color": None,
        }

        # Get background color
        background = self.get_background_color(index)
        if background:
            metadata["background"] = background.name()

        # Get text color based on background
        foreground = self.data(index, Qt.ForegroundRole)
        if isinstance(foreground, QBrush):
            metadata["text_color"] = foreground.color().name()

        return metadata

    def get_table_state(self):
        """Extract complete table state including content and formatting."""
        data = []
        metadata = []
        row_highlights = []

        for row in range(self.rowCount()):
            data_row = []
            metadata_row = []
            row_highlight = None

            for col in range(self.columnCount()):
                index = self.index(row, col)
                cell_metadata = self.get_cell_metadata(index)

                # Add value to data
                data_row.append(cell_metadata["value"])

                # Add formatting to metadata
                metadata_row.append(
                    {
                        "background": cell_metadata["background"],
                        "text_color": cell_metadata["text_color"],
                    }
                )

                # Check for row highlight (SUMMARY_ROW_COLOR)
                if cell_metadata["background"] == SUMMARY_ROW_COLOR.name():
                    row_highlight = cell_metadata["background"]

            data.append(data_row)
            metadata.append(metadata_row)
            row_highlights.append(row_highlight)

        # Convert to DataFrames
        headers = [
            self.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            for col in range(self.columnCount())
        ]

        content_df = pd.DataFrame(data, columns=headers)
        metadata_df = pd.DataFrame(metadata, columns=headers)
        row_highlights_df = pd.Series(row_highlights, name="row_highlight")

        return content_df, metadata_df, row_highlights_df

    def sort(self, column, order):
        """Override sort to use numeric sorting for numeric columns."""
        try:
            self.layoutAboutToBeChanged.emit()
            header = self.headerData(column, Qt.Horizontal, Qt.DisplayRole)

            # Get the actual column name from the DataFrame
            df_column = self.df.columns[column]

            # List of columns that should be sorted numerically
            # (includes both display names and df names)
            numeric_columns = {
                "Weekly Remedy Total",
                "Remedy Total",
                "Own Route Hours",
                "Off Route Hours",
                "Total Hours",
                "Daily Hours",
                "Cumulative Hours",
                "weekly_remedy_total",
                "remedy_total",
                "own_route_hours",
                "off_route_hours",
                "total_hours",
                "daily_hours",
                "cumulative_hours",
            }

            if header in numeric_columns or df_column in numeric_columns:
                # Sort using the numeric values
                self.df = self.df.sort_values(
                    by=df_column,
                    ascending=order == Qt.AscendingOrder,
                    na_position="last",
                )
            else:
                # Regular string sorting for non-numeric columns
                self.df = self.df.sort_values(
                    by=df_column,
                    ascending=order == Qt.AscendingOrder,
                    na_position="last",
                )

            # Refresh the model after sorting
            self.setup_model()
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Sorting error: {e}")


class ViolationFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering violation data in table views.

    Provides filtering capabilities for:
    - Carrier name (case-insensitive substring match)
    - List status (exact match)
    - Violation presence (shows only rows with violations)

    Attributes:
        filter_type (str): Type of filter to apply ('name', 'list_status', 'violations')
        filter_text (str): Text to filter by (lowercase)
    """

    def __init__(self):
        super().__init__()
        self.filter_type = "name"
        self.filter_text = ""
        self.setSortRole(Qt.UserRole)

    def set_filter(self, text, filter_type="name"):
        self.filter_type = filter_type
        self.filter_text = text.lower() if text else ""
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()

        if not self.filter_text and self.filter_type != "violations":
            return True

        if self.filter_type == "list_status":
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                # Check for both original and renamed column names
                if header and header.lower() in ["list status", "list_status"]:
                    idx = source_model.index(source_row, col, source_parent)
                    list_status = source_model.data(idx, Qt.DisplayRole)
                    if list_status:
                        return str(list_status).lower() == self.filter_text

        elif self.filter_type == "name":
            # Check for both "Carrier Name" and "carrier_name"
            for col in range(source_model.columnCount()):
                header = source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() in ["carrier name", "carrier_name"]:
                    idx = source_model.index(source_row, col, source_parent)
                    name = source_model.data(idx, Qt.DisplayRole)
                    if name:
                        return self.filter_text in str(name).lower()
            # Fallback to first column if no carrier name column found
            idx = source_model.index(source_row, 0, source_parent)
            name = source_model.data(idx, Qt.DisplayRole)
            if name:
                return self.filter_text in str(name).lower()

        elif self.filter_type == "violations":
            # Check for Weekly Remedy Total column first (Summary tab)
            for col in range(source_model.columnCount()):
                header = str(
                    source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                )
                if header in ["Weekly Remedy Total", "Remedy Total"]:
                    idx = source_model.index(source_row, col, source_parent)
                    value = source_model.data(idx, Qt.DisplayRole)
                    try:
                        return float(str(value).replace(",", "")) > 0.00
                    except (ValueError, TypeError):
                        return False

            # If not found, check violation_type (Daily tabs)
            for col in range(source_model.columnCount()):
                header = str(
                    source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                )
                if header in ["violation_type", "Violation Type"]:
                    idx = source_model.index(source_row, col, source_parent)
                    value = str(source_model.data(idx, Qt.DisplayRole))
                    return value != "No Violation"

        return True
