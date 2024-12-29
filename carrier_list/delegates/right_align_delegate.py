"""Custom delegate for right-aligned text in table cells."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyledItemDelegate


class RightAlignDelegate(QStyledItemDelegate):
    """Custom delegate for right-aligned text in table cells."""

    def initStyleOption(self, option, index):
        """Initialize style options for the delegate.

        Args:
            option (QStyleOptionViewItem): The style options to initialize
            index (QModelIndex): The index being styled
        """
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignRight | Qt.AlignVCenter
