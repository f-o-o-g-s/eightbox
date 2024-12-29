"""Data model for displaying pandas DataFrames in Qt table views."""

import pandas as pd
from PyQt5.QtCore import (
    QAbstractTableModel,
    Qt,
    QVariant,
)
from PyQt5.QtGui import QColor

from theme import (
    COLOR_BLACK,
    COLOR_STATUS_NL,
    COLOR_STATUS_OTDL,
    COLOR_STATUS_PTF,
    COLOR_STATUS_WAL,
    COLOR_WHITE,
)

# Map carrier list status to colors
STATUS_COLORS = {
    "otdl": COLOR_STATUS_OTDL,  # Purple
    "wal": COLOR_STATUS_WAL,  # Teal
    "nl": COLOR_STATUS_NL,  # Light Green
    "ptf": COLOR_STATUS_PTF,  # Pink
}


class PandasTableModel(QAbstractTableModel):
    """Table model for displaying pandas DataFrame in a QTableView.

    Handles data display, editing, and formatting for carrier information
    including status colors and text alignment.
    """

    def __init__(self, df, db_df=None, parent=None):
        super().__init__(parent)
        self.df = df
        self.db_df = db_df if db_df is not None else pd.DataFrame()
        # Define text colors for different list statuses using theme constants
        self.status_text_colors = STATUS_COLORS

    def calculate_text_color(self, bg_color):
        """Calculate optimal text color (black or white) based on background color.

        Uses relative luminance formula to determine best contrast.

        Args:
            bg_color (QColor): Background color to calculate against

        Returns:
            QColor: Either black or white depending on background
        """
        # Convert RGB values to relative luminance
        r = bg_color.red() / 255.0
        g = bg_color.green() / 255.0
        b = bg_color.blue() / 255.0

        # Calculate relative luminance using sRGB formula
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Return white for dark backgrounds, black for light backgrounds
        return COLOR_WHITE if luminance < 0.5 else COLOR_BLACK

    def update_data(self, new_df, new_db_df=None):
        """Update the model's data with new DataFrame(s).

        Args:
            new_df (pd.DataFrame): New carrier data to display
            new_db_df (pd.DataFrame, optional): New database reference data
        """
        self.beginResetModel()
        self.df = new_df
        if new_db_df is not None:
            self.db_df = new_db_df
        self.endResetModel()

    def rowCount(self, parent=None):
        """Get the number of rows in the model.

        Args:
            parent (QModelIndex): Parent index (unused in table models)

        Returns:
            int: Number of rows in the carrier data
        """
        return len(self.df)

    def columnCount(self, parent=None):
        """Get the number of columns in the model.

        Args:
            parent (QModelIndex): Parent index (unused in table models)

        Returns:
            int: Number of columns in the carrier data
        """
        return len(self.df.columns)

    def data(self, index, role=Qt.DisplayRole):
        """Get data for the specified model index and role."""
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            value = self.df.iloc[index.row(), index.column()]
            # Format hour_limit with 2 decimal places
            if self.df.columns[index.column()] == "hour_limit":
                return f"{float(value):.2f}" if pd.notna(value) else ""
            return str(value) if pd.notna(value) else ""

        elif role == Qt.ForegroundRole:
            # Get list_status for this row
            list_status = str(self.df.iloc[index.row()]["list_status"]).lower().strip()
            # Return the text color for this status
            return self.status_text_colors.get(list_status, QColor("#FFFFFF"))

        elif role == Qt.TextAlignmentRole:
            # Right-align the hour_limit column
            if self.df.columns[index.column()] == "hour_limit":
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return QVariant()

    def headerData(self, section, orientation, role):
        """Get header data for display.

        Provides column and row headers for the carrier list table.

        Args:
            section (int): Section (row/column) number
            orientation (Qt.Orientation): Header orientation
            role (Qt.ItemDataRole): Data role being requested

        Returns:
            str: Header text for DisplayRole, None for other roles
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.df.columns[section]
            if orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        """Set data in the model.

        Updates the model data and handles any necessary post-update actions.

        Args:
            index (QModelIndex): The index to update
            value (Any): The new value to set
            role (Qt.ItemRole): The role being set (default: EditRole)

        Returns:
            bool: True if data was successfully set, False otherwise
        """
        if role == Qt.EditRole and index.isValid():
            column = self.df.columns[index.column()]
            current_value = self.df.iloc[index.row(), index.column()]

            if current_value != value:
                self.df.iloc[index.row(), index.column()] = value

                # Track changed rows
                if not hasattr(self, "changed_rows"):
                    self.changed_rows = set()
                self.changed_rows.add(index.row())

                # Notify the view of data changes
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.BackgroundRole])
                print(f"Edited {column} for row {index.row()}, new value: {value}")
                return True
        return False

    def flags(self, index):
        """Return item flags for the given index."""
        # Remove ItemIsEditable flag to prevent direct editing
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
