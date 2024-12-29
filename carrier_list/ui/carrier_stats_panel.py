"""Statistics panel for carrier list display."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)

from ..ui.styles import STATS_PANEL_STYLE


class CarrierStatsPanel(QWidget):
    """Panel displaying carrier statistics and filter buttons.

    Shows counts for different carrier list statuses and provides
    filtering functionality.
    """

    status_filter_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize the statistics panel.

        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the panel's user interface."""
        self.setStyleSheet(STATS_PANEL_STYLE)
        layout = QHBoxLayout(self)
        layout.setSpacing(20)  # Space between stat items
        layout.setContentsMargins(8, 4, 8, 4)  # Tighter margins

        # Initialize statistics labels and values
        self.total_value = QLabel("0")
        self.total_value.setProperty("class", "stat-value")
        self.total_value.setProperty("status", "all")

        self.otdl_value = QLabel("0")
        self.otdl_value.setProperty("class", "stat-value")
        self.otdl_value.setProperty("status", "otdl")

        self.wal_value = QLabel("0")
        self.wal_value.setProperty("class", "stat-value")
        self.wal_value.setProperty("status", "wal")

        self.nl_value = QLabel("0")
        self.nl_value.setProperty("class", "stat-value")
        self.nl_value.setProperty("status", "nl")

        self.ptf_value = QLabel("0")
        self.ptf_value.setProperty("class", "stat-value")
        self.ptf_value.setProperty("status", "ptf")

        # Add stretch before the stats to push them to center
        layout.addStretch()

        # Create labels for statistics in a more compact layout
        for label_text, value_widget, status in [
            ("ALL", self.total_value, "all"),
            ("OTDL", self.otdl_value, "otdl"),
            ("WAL", self.wal_value, "wal"),
            ("NL", self.nl_value, "nl"),
            ("PTF", self.ptf_value, "ptf"),
        ]:
            stat_container = QWidget()
            stat_container.setProperty("class", "stat-container")
            stat_container.setProperty("selected", False)
            stat_layout = QHBoxLayout(stat_container)
            stat_layout.setContentsMargins(4, 4, 4, 4)
            stat_layout.setSpacing(4)  # Tighter spacing

            label = QLabel(label_text)
            stat_layout.addWidget(label)
            stat_layout.addWidget(value_widget)

            stat_container.status = status
            stat_container.mousePressEvent = lambda e, s=status: self.filter_by_status(
                s
            )
            layout.addWidget(stat_container)
            setattr(self, f"{status}_container", stat_container)

        # Add stretch after the stats to push them to center
        layout.addStretch()

    def update_stats(self, total, otdl, wal, nl, ptf):
        """Update the displayed statistics.

        Args:
            total (int): Total number of carriers
            otdl (int): Number of OTDL carriers
            wal (int): Number of WAL carriers
            nl (int): Number of NL carriers
            ptf (int): Number of PTF carriers
        """
        self.total_value.setText(str(total))
        self.otdl_value.setText(str(otdl))
        self.wal_value.setText(str(wal))
        self.nl_value.setText(str(nl))
        self.ptf_value.setText(str(ptf))

    def filter_by_status(self, status):
        """Apply filter by carrier status.

        Args:
            status (str): Status to filter by ('all', 'otdl', 'wal', 'nl', 'ptf')
        """
        # Clear previous selection states
        for s in ["all", "otdl", "wal", "nl", "ptf"]:
            container = getattr(self, f"{s}_container")
            container.setProperty("selected", False)
            container.style().unpolish(container)
            container.style().polish(container)

        # Set new selection state
        container = getattr(self, f"{status}_container")
        container.setProperty("selected", True)
        container.style().unpolish(container)
        container.style().polish(container)

        # Emit signal for status change
        self.status_filter_changed.emit(status)
