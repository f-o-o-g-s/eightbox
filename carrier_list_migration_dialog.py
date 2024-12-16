"""Dialog for handling carrier list migration between databases.

This module provides a dialog interface for users to:
- View carrier differences when changing databases
- Backup existing carrier list
- Start fresh with new database carriers
"""

import os
import shutil
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import CustomTitleBarWidget


class CarrierListMigrationDialog(QDialog):
    """Dialog for managing carrier list migration between databases.

    Provides a simple interface to:
    - View carrier differences
    - Backup existing carrier list
    - Start fresh with new database
    """

    def __init__(self, existing_carriers, new_carriers, parent=None):
        super().__init__(parent)
        self.existing_carriers = existing_carriers
        self.new_carriers = new_carriers
        self.selected_option = "start_fresh"  # Always start fresh
        self.should_backup = True  # Always backup by default

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setMinimumWidth(600)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
            }
            QTableWidget {
                background-color: #2D2D2D;
                color: #FFFFFF;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #FFFFFF;
                padding: 5px;
                border: none;
            }
            QPushButton {
                background-color: #9575CD;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #B39DDB;
            }
            QPushButton:pressed {
                background-color: #7E57C2;
            }
        """
        )

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(
            title="New Database Detected", parent=self
        )
        layout.addWidget(self.title_bar)

        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Add explanation label
        explanation = QLabel(
            "A new database has been selected with different carriers.\n"
            "Your existing carrier list will be backed up, and a new list will be created\n"
            "with carriers from the new database."
        )
        explanation.setWordWrap(True)
        content_layout.addWidget(explanation)

        # Add carrier comparison table
        content_layout.addWidget(QLabel("Carrier Differences:"))
        self.comparison_table = self.create_comparison_table()

        # Create scroll area for table
        scroll = QScrollArea()
        scroll.setWidget(self.comparison_table)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        content_layout.addWidget(scroll)

        # Add buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        content_layout.addLayout(button_layout)

        # Add content to main layout
        layout.addWidget(content)

    def create_comparison_table(self):
        """Create a table showing carrier differences between databases."""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(
            ["Carrier Name", "Current Status", "New Status"]
        )

        # Get all unique carrier names
        all_carriers = set()
        for carrier in self.existing_carriers:
            all_carriers.add(carrier["carrier_name"])
        for carrier in self.new_carriers:
            all_carriers.add(carrier["carrier_name"])

        # Sort carriers alphabetically
        all_carriers = sorted(all_carriers)

        # Create lookup dictionaries
        existing_dict = {
            c["carrier_name"]: c["list_status"] for c in self.existing_carriers
        }
        new_dict = {c["carrier_name"]: c["list_status"] for c in self.new_carriers}

        # Populate table
        table.setRowCount(len(all_carriers))
        for i, carrier in enumerate(all_carriers):
            # Carrier name
            name_item = QTableWidgetItem(carrier)
            table.setItem(i, 0, name_item)

            # Current status
            current_status = existing_dict.get(carrier, "Not present")
            current_item = QTableWidgetItem(current_status)
            table.setItem(i, 1, current_item)

            # New status
            new_status = new_dict.get(carrier, "Not present")
            new_item = QTableWidgetItem(new_status)
            table.setItem(i, 2, new_item)

            # Highlight differences
            if current_status != new_status:
                for col in range(3):
                    item = table.item(i, col)
                    item.setBackground(Qt.darkRed)

        # Adjust column widths
        table.resizeColumnsToContents()
        return table

    def accept(self):
        """Handle dialog acceptance."""
        # Create backup if requested
        if os.path.exists("carrier_list.json"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"carrier_list_{timestamp}.json.bak"
            try:
                shutil.copy2("carrier_list.json", backup_path)
            except Exception as e:
                print(f"Warning: Failed to create backup: {e}")

        super().accept()

    def get_result(self):
        """Get the dialog results.

        Returns:
            tuple: (selected_option, should_backup)
        """
        return self.selected_option, self.should_backup
