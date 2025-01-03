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

from theme import (
    VIOLATION_MODEL_COLORS,
    calculate_optimal_gray,
)
from violation_types import ViolationType

# We can remove the theme import entirely since we're calculating all text colors dynamically

# fully opaque
VIOLATION_COLOR = VIOLATION_MODEL_COLORS["violation"]
# Softer background for summary rows with violations
SUMMARY_ROW_COLOR = VIOLATION_MODEL_COLORS["summary"]
# Teal color for positive weekly totals
WEEKLY_TOTAL_COLOR = VIOLATION_MODEL_COLORS["weekly"]


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
        """Get data for display in the violation table.

        Handles different display roles including:
        - DisplayRole: Formatted cell values
        - BackgroundRole: Cell background colors
        - ForegroundRole: Text colors
        - UserRole: Sorting values

        Args:
            index (QModelIndex): The cell index
            role (Qt.ItemDataRole): The role being requested

        Returns:
            Various: Data appropriate for the requested role, or None if invalid
        """
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
        col_name = self.header_data(col, Qt.Horizontal, Qt.DisplayRole)
        value = self.data(index, Qt.DisplayRole)

        # Start with row-level highlighting for violations
        background_color = SUMMARY_ROW_COLOR if self.has_violation_in_row(row) else None

        # Add ViolationRemedies tab type handling
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
                if col_name not in ["carrier_name", "list_status"]:
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
                if col_name not in ["carrier_name", "list_status"]:
                    try:
                        number = float(str(value))
                        if number > 0:
                            return VIOLATION_COLOR
                    except (ValueError, TypeError):
                        pass

        # Then apply specific cell colors that should override the row highlight
        if self.tab_type == ViolationType.EIGHT_FIVE_D:
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
                if col_name not in [
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

        # Then apply specific cell colors that should override the row highlight
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
                # Individual day columns in darker purple only for violation date
                elif col_name not in ["Carrier Name", "List Status"]:
                    try:
                        # Get the carrier's row data
                        row_data = self.df.iloc[index.row()]
                        violation_date = row_data.get("85F_5th_date", None)

                        # Only highlight if this column is the violation date
                        if violation_date and str(col_name) == str(violation_date):
                            try:
                                number = float(str(value))
                                if number > 0:
                                    return VIOLATION_COLOR
                            except (ValueError, TypeError):
                                pass
                    except (ValueError, TypeError, AttributeError, KeyError):
                        pass
            else:
                # Daily tab formatting
                if col_name == "Remedy Total" and value:
                    try:
                        if float(str(value)) > 0:
                            return VIOLATION_COLOR
                    except ValueError:
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
                # Highlight Total Weekly Hours > 60 in darker purple (except for PTF)
                elif col_name == "Total Weekly Hours":
                    try:
                        # Find list status column by checking headers
                        list_status_col = None
                        for i in range(self.columnCount()):
                            header = self.header_data(i, Qt.Horizontal, Qt.DisplayRole)
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

        elif self.tab_type == ViolationType.EIGHT_FIVE_G:
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
                    "Hour Limit",
                    "Trigger Carrier",
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

        return background_color

    def has_violation_in_row(self, row):
        """Check if the row contains any violations."""
        # First check violation_type column if it exists
        for col in range(self.columnCount()):
            header = self.header_data(col, Qt.Horizontal, Qt.DisplayRole)
            if header in ["violation_type", "Violation Type"]:
                value = self.data(self.index(row, col), Qt.DisplayRole)
                if value and not value.startswith("No Violation"):
                    return True
                break  # Exit after checking violation_type

        # Then check remedy total columns
        for col in range(self.columnCount()):
            header = self.header_data(col, Qt.Horizontal, Qt.DisplayRole)
            if header in ["Weekly Remedy Total", "Remedy Total"]:
                value = self.data(self.index(row, col), Qt.DisplayRole)
                if value:  # Only check if value is not empty
                    try:
                        if float(str(value).replace(",", "")) > 0.00:
                            return True
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
                item = QStandardItem(str(value) if pd.notna(value) else "")
                self.setItem(row, col, item)

    def get_violation_column(self):
        """Get the index of the violation_type column."""
        try:
            return self.df.columns.get_loc("violation_type")
        except KeyError:
            # If violation_type column doesn't exist, return carrier_name column (0)
            return 0

    def header_data(self, section, orientation, role=Qt.DisplayRole):
        """Override header_data to display the column names from the DataFrame."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self.df.columns):
                return str(self.df.columns[section])
        return super().header_data(section, orientation, role)

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
        """Get the complete state of the table for Excel export.

        This method is REQUIRED for Excel export functionality.
        It must return three DataFrames containing:
        1. The actual cell values
        2. Cell metadata (colors, formatting)
        3. Row-level highlight information

        Returns:
            tuple: (content_df, metadata_df, row_highlights_df)
                - content_df: DataFrame with actual cell values
                - metadata_df: DataFrame with cell formatting info
                - row_highlights_df: DataFrame with row highlight info
        """
        # Get headers from the model
        headers = [
            self.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            for col in range(self.columnCount())
        ]

        # Build content DataFrame from actual displayed values
        content_data = []
        metadata_data = []

        for row in range(self.rowCount()):
            row_content = []
            row_metadata = []
            for col in range(self.columnCount()):
                index = self.index(row, col)
                # Get display value
                value = self.data(index, Qt.DisplayRole)
                row_content.append(value)

                # Get cell metadata
                bg_color = self.get_background_color(index)
                fg_color = self.get_foreground_color(index)

                metadata = {
                    "background": bg_color.name() if bg_color else None,
                    "foreground": fg_color.name() if fg_color else None,
                }
                row_metadata.append(metadata)

            content_data.append(row_content)
            metadata_data.append(row_metadata)

        # Create DataFrames
        content_df = pd.DataFrame(content_data, columns=headers)
        metadata_df = pd.DataFrame(metadata_data, columns=headers)

        # Create row highlights DataFrame
        row_highlights = []
        for row in range(self.rowCount()):
            has_highlight = self.has_violation_in_row(row)
            row_highlights.append({"row": row, "highlighted": has_highlight})
        row_highlights_df = pd.DataFrame(row_highlights)

        return content_df, metadata_df, row_highlights_df

    def sort(self, column, order):
        """Override sort to use numeric sorting for numeric columns."""
        try:
            self.layoutAboutToBeChanged.emit()
            header = self.header_data(column, Qt.Horizontal, Qt.DisplayRole)

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

    def get_violation_type_display(self, violation_type):
        """Get the display name for a violation type.

        Converts internal violation type codes to human-readable display names.

        Args:
            violation_type (str): The internal violation type code

        Returns:
            str: The human-readable display name for the violation type
        """


class ViolationFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering violation data in table views.

    Provides filtering capabilities for:
    - Carrier name (case-insensitive substring match)
    - List status (exact match)
    - Violation presence (shows only rows with violations)
    - Column visibility control

    Attributes:
        filter_type (str): Type of filter to apply ('name', 'list_status', 'violations')
        filter_text (str): Text to filter by (lowercase)
        hidden_columns (set): Set of column names to hide
    """

    def __init__(self):
        super().__init__()
        self.filter_type = "name"
        self.filter_text = ""
        self.hidden_columns = set()
        self.setSortRole(Qt.UserRole)

    def set_hidden_columns(self, columns):
        """Set columns to hide from view.

        Args:
            columns (list): List of column names to hide
        """
        self.hidden_columns = set(columns)
        self.invalidateFilter()

    def filter_accepts_column(self, source_column, _):
        """Determine if a column should be shown in the view.

        Args:
            source_column (int): Column index in source model
            _: Unused parent index parameter

        Returns:
            bool: True if column should be shown, False if hidden
        """
        source_model = self.sourceModel()
        if source_model:
            column_name = source_model.header_data(
                source_column, Qt.Horizontal, Qt.DisplayRole
            )
            return column_name not in self.hidden_columns
        return True

    def filter_accepts_row(self, source_row, source_parent):
        """Determine if a row should be included in the filtered view.

        Implements the filtering logic for violations based on:
        - List status (WAL, NL, OTDL, etc.)
        - Violation type
        - Custom text filters

        Args:
            source_row (int): Row index in the source model
            source_parent (QModelIndex): Parent index in source model

        Returns:
            bool: True if row should be shown, False if filtered out
        """
        source_model = self.sourceModel()

        if not self.filter_text and self.filter_type != "violations":
            return True

        if self.filter_type == "name":
            # Get carrier name column
            carrier_col = None
            for col in range(source_model.columnCount(source_parent)):
                header = source_model.header_data(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() in ["carrier_name", "carrier name"]:
                    carrier_col = col
                    break

            if carrier_col is not None:
                idx = source_model.index(source_row, carrier_col, source_parent)
                name = str(source_model.data(idx, Qt.DisplayRole)).lower()
                return self.filter_text in name
            return False

        elif self.filter_type == "list_status":
            # Get list status column
            status_col = None
            for col in range(source_model.columnCount(source_parent)):
                header = source_model.header_data(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() in ["list_status", "list status"]:
                    status_col = col
                    break

            if status_col is not None:
                idx = source_model.index(source_row, status_col, source_parent)
                status = str(source_model.data(idx, Qt.DisplayRole)).lower()
                return status == self.filter_text
            return False

        elif self.filter_type == "violations":
            # Check remedy total column
            remedy_col = None
            for col in range(source_model.columnCount(source_parent)):
                header = source_model.header_data(col, Qt.Horizontal, Qt.DisplayRole)
                if header and header.lower() in ["remedy_total", "remedy total"]:
                    remedy_col = col
                    break

            if remedy_col is not None:
                idx = source_model.index(source_row, remedy_col, source_parent)
                remedy = source_model.data(idx, Qt.DisplayRole)
                try:
                    return float(str(remedy).split()[0]) > 0
                except (ValueError, TypeError, IndexError):
                    return False
            return False

        return True
