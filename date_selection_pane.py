"""Date selection component for the application.

Provides a table interface for selecting date ranges, showing only valid ranges 
that have data in the database.
"""

from datetime import datetime, timedelta
import sqlite3

from PyQt5.QtCore import (
    Qt,
    QModelIndex,
    pyqtSignal,
    QAbstractTableModel,
    QDate,
)
from PyQt5.QtGui import (
    QColor,
)
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
    QSizePolicy,
)

from custom_widgets import CustomTitleBarWidget


class DateRangeModel(QAbstractTableModel):
    """Model for storing and managing date range data in a table structure."""

    def __init__(self):
        super().__init__()
        self.headers = ["Date Range", "Year", "Carriers"]
        self.date_ranges = []  # Will store tuples of (start_date, end_date, carrier_count)

    def rowCount(self, parent=None):
        return len(self.date_ranges)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            start_date, end_date, carrier_count = self.date_ranges[row]
            if col == 0:
                return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            elif col == 1:
                return start_date.strftime("%Y")
            elif col == 2:
                return str(carrier_count)

        elif role == Qt.TextAlignmentRole:
            if col == 2:  # Carriers column
                return Qt.AlignCenter
            elif col == 1:  # Year column
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.BackgroundRole:
            # Alternate row colors for better readability
            if row % 2:
                return QColor("#2A2A2A")
            return QColor("#222222")

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def populate_data(self, date_ranges):
        """Populate the model with date range data.
        
        Args:
            date_ranges: List of tuples (start_date, end_date, carrier_count)
                        where dates are datetime objects
        """
        self.beginResetModel()
        self.date_ranges = date_ranges
        self.endResetModel()

    def get_date_range(self, row):
        """Get the date range for a specific row.
        
        Args:
            row: The row index
            
        Returns:
            tuple: (start_date, end_date) or None if invalid row
        """
        if 0 <= row < len(self.date_ranges):
            start_date, end_date, _ = self.date_ranges[row]
            return start_date, end_date
        return None


class DateRangeSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        # Main layout with no spacing or margins
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Create and set up the table view
        self.table_view = QTableView()
        self.model = DateRangeModel()
        self.table_view.setModel(self.model)

        # Configure table view properties
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setShowGrid(False)
        
        # Set up the header and column sizes
        header = self.table_view.horizontalHeader()
        
        # Make Date Range column stretch to fill available space
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        
        # Set fixed widths for Year and Carriers columns
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_view.setColumnWidth(1, 80)   # Year column
        self.table_view.setColumnWidth(2, 100)  # Carriers column

        # Make the table view stretch to fill available space
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table_view)

        # Connect selection signal
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        """Handle selection changes in the table view."""
        if selected.indexes():
            row = selected.indexes()[0].row()
            start_date, end_date, _ = self.model.date_ranges[row]
            self.date_range_selected.emit(start_date, end_date)

    # Signal emitted when a date range is selected
    date_range_selected = pyqtSignal(QDate, QDate)


class DateSelectionPane(QWidget):
    """A widget for selecting date ranges from available data.

    Provides a table interface showing available date ranges with carrier counts.
    """
    
    date_range_selected = pyqtSignal(datetime, datetime)  # Emits (start_date, end_date)

    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.parent_widget = parent
        self.selected_range = None
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("Date Range Selection", self)
        layout.addWidget(self.title_bar)

        # Content widget with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Current selection label
        self.selection_label = QLabel("No Date Range Selected")
        content_layout.addWidget(self.selection_label)

        # Table view
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        
        # Set up the model
        self.model = DateRangeModel()
        self.table_view.setModel(self.model)
        
        # Set up header
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Date Range
        header.setSectionResizeMode(1, QHeaderView.Fixed)   # Year
        header.setSectionResizeMode(2, QHeaderView.Fixed)   # Carriers
        
        # Set fixed widths for Year and Carriers columns
        self.table_view.setColumnWidth(1, 80)   # Year
        self.table_view.setColumnWidth(2, 100)  # Carriers
        
        # Hide vertical header (row numbers)
        self.table_view.verticalHeader().hide()
        
        # Make the table view stretch to fill available space
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.table_view)

        # Connect selection signal
        self.table_view.clicked.connect(self.handle_selection)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.apply_button = QPushButton("Apply Selection")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_selection)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.refresh_button)
        
        content_layout.addLayout(button_layout)
        
        # Make content widget stretch
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(content_widget)

    def load_data(self):
        """Load date ranges from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        DATE(rings_date) as rings_date,
                        COUNT(DISTINCT carrier_name) as carrier_count
                    FROM rings3 
                    GROUP BY DATE(rings_date)
                    ORDER BY rings_date DESC
                """)
                
                # Process results into weekly ranges
                date_ranges = []
                current_start = None
                current_carriers = 0
                
                for row in cursor.fetchall():
                    date_str, carrier_count = row
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # If it's a Saturday, start a new range
                    if date.weekday() == 5:  # 5 = Saturday
                        if current_start:
                            # Add the previous range
                            date_ranges.append((
                                current_start,
                                current_start + timedelta(days=6),
                                current_carriers
                            ))
                        current_start = date
                        current_carriers = carrier_count
                
                # Add the last range if there is one
                if current_start:
                    date_ranges.append((
                        current_start,
                        current_start + timedelta(days=6),
                        current_carriers
                    ))
                
                # Update the model
                self.model.populate_data(date_ranges)
                
        except Exception as e:
            print(f"Error loading date ranges: {e}")

    def handle_selection(self, index):
        """Handle selection in the table view."""
        row = index.row()
        date_range = self.model.get_date_range(row)
        
        if date_range:
            start_date, end_date = date_range
            self.selected_range = (start_date, end_date)
            self.selection_label.setText(
                f"Selected: {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            )
            self.apply_button.setEnabled(True)
        else:
            self.selected_range = None
            self.apply_button.setEnabled(False)

    def apply_selection(self):
        """Apply the selected date range."""
        if self.selected_range:
            start_date, end_date = self.selected_range
            self.date_range_selected.emit(start_date, end_date) 