"""Table view for displaying carrier information."""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QHeaderView,
    QTableView,
)

from ..delegates.right_align_delegate import RightAlignDelegate
from ..ui.styles import TABLE_VIEW_STYLE


class CarrierTableView(QTableView):
    """Custom table view for displaying carrier information.

    Provides a styled table view with proper column sizing and alignment.
    """

    def __init__(self, parent=None):
        """Initialize the table view.

        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the table view's user interface."""
        # Set basic table properties
        self.setEditTriggers(QTableView.NoEditTriggers)  # Disable all editing
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setVisible(False)  # Hide row numbers

        # Set the table to stretch to fill the window
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Apply styling
        self.setStyleSheet(TABLE_VIEW_STYLE)

        # Set up columns after a short delay to ensure proper sizing
        QTimer.singleShot(0, self.setup_columns)

    def setup_columns(self):
        """Set up column widths and alignment."""
        # Set column widths proportionally
        total_width = max(self.width(), 800)  # Use at least 800px as base width

        # Reset all columns to Interactive mode first
        for i in range(5):  # We know we have 5 columns
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)

        # Hide the effective_date column
        self.hideColumn(1)

        # Set initial column widths (matching old implementation exactly)
        self.setColumnWidth(0, int(total_width * 0.25))  # carrier_name
        self.setColumnWidth(2, int(total_width * 0.15))  # list_status
        self.setColumnWidth(3, int(total_width * 0.20))  # route_s

        # Set the last column to stretch after setting explicit widths
        self.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.Stretch
        )  # hour_limit

        # Right-align the hour_limit column using our custom delegate
        self.setItemDelegateForColumn(4, RightAlignDelegate(self))

    def resizeEvent(self, event):
        """Handle resize events to maintain column proportions.

        Args:
            event: The resize event
        """
        super().resizeEvent(event)
        self.setup_columns()
