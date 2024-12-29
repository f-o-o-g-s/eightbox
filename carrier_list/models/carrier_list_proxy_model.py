"""Proxy model for filtering and sorting carrier list data."""

from PyQt5.QtCore import (
    QSortFilterProxyModel,
    Qt,
)


class CarrierListProxyModel(QSortFilterProxyModel):
    """Custom proxy model for filtering and sorting carrier list data.

    Provides custom sorting for list status and carrier names, along with
    filtering capabilities for both status and text searches.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_filter = ""
        self.text_filter = ""
        # Define status order for sorting
        self.status_order = {"nl": 0, "wal": 1, "otdl": 2, "ptf": 3}

    def set_text_filter(self, text):
        """Set the text filter and invalidate the current filtering."""
        self.text_filter = text.lower()
        self.invalidateFilter()

    def set_status_filter(self, status):
        """Set the status filter and invalidate the current filtering."""
        self.status_filter = status if status != "all" else ""
        self.invalidateFilter()

    def lessThan(self, left, right):
        """Custom sorting implementation"""
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        # Get column name
        column_name = self.sourceModel().headerData(
            left.column(), Qt.Horizontal, Qt.DisplayRole
        )

        if column_name == "list_status":
            # Use custom status ordering
            left_order = self.status_order.get(str(left_data).lower(), 999)
            right_order = self.status_order.get(str(right_data).lower(), 999)
            if left_order != right_order:
                return left_order < right_order
            # If list_status is the same, sort by carrier_name
            carrier_col = self.sourceModel().df.columns.get_loc("carrier_name")
            left_carrier = str(
                self.sourceModel().data(
                    self.sourceModel().index(left.row(), carrier_col),
                    Qt.DisplayRole,
                )
            ).lower()
            right_carrier = str(
                self.sourceModel().data(
                    self.sourceModel().index(right.row(), carrier_col),
                    Qt.DisplayRole,
                )
            ).lower()
            return left_carrier < right_carrier

        # For carrier_name column, ensure ascending order
        if column_name == "carrier_name":
            return str(left_data).lower() < str(right_data).lower()
        # For other columns, use standard comparison
        return str(left_data).lower() < str(right_data).lower()

    def filterAcceptsRow(self, source_row, source_parent):
        """Determine if a row should be included in the filtered results."""
        source_model = self.sourceModel()

        # Get the list status for this row
        status_idx = source_model.index(
            source_row,
            self.sourceModel().df.columns.get_loc("list_status"),
            source_parent,
        )
        status = str(source_model.data(status_idx, Qt.DisplayRole)).lower()

        # Check status filter
        if self.status_filter and status != self.status_filter:
            return False

        # If there's no text filter, we're done
        if not self.text_filter:
            return True

        # Check text filter against all columns
        for column in range(source_model.columnCount(source_parent)):
            idx = source_model.index(source_row, column, source_parent)
            data = str(source_model.data(idx, Qt.DisplayRole)).lower()
            if self.text_filter in data:
                return True

        return False
