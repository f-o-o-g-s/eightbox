"""Manages the list of removed carriers.

This module provides functionality to view and manage carriers that have been
removed from the carrier list.
"""

import sqlite3

import pandas as pd
from PyQt5.QtCore import (
    QAbstractTableModel,
    Qt,
)
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    CustomNotificationDialog,
    CustomTitleBarWidget,
    CustomWarningDialog,
)


class RemovedCarriersTableModel(QAbstractTableModel):
    """Table model for displaying removed carriers data."""

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            value = self._df.iloc[index.row(), index.column()]
            return str(value)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter  # Center align both horizontally and vertically

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # Return formatted column names
                col_name = self._df.columns[section]
                return col_name.replace("_", " ").title()
            if orientation == Qt.Vertical:
                return str(section + 1)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter  # Center align headers too
        return None


class RemovedCarriersManager(QDialog):
    """Dialog for managing removed carriers.

    Provides a UI for viewing and restoring carriers that have been removed from the list.

    Attributes:
        eightbox_db_path (str): Path to the eightbox database
        parent_widget: Parent widget for the dialog
    """

    def __init__(self, eightbox_db_path, parent=None):
        super().__init__(parent)
        self.eightbox_db_path = eightbox_db_path
        self.parent_widget = parent
        self.mandates_db_path = getattr(parent, "mandates_db_path", None)
        self.json_path = "carrier_list.json"
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        title_bar = CustomTitleBarWidget("Removed Carriers Manager", self)
        layout.addWidget(title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                color: #E1E1E1;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
                padding: 4px;
            }
            QTableView {
                background-color: #1E1E1E;
                alternate-background-color: #262626;
                border: 1px solid #333333;
                border-radius: 4px;
                gridline-color: #333333;
            }
            QTableView::item {
                padding: 8px;
                border: none;
            }
            QTableView::item:selected {
                background-color: #BB86FC;
                color: black;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E1E1E1;
                padding: 8px;
                border: none;
                border-right: 1px solid #333333;
                border-bottom: 1px solid #333333;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            """
        )

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Add description label
        description = QLabel(
            "These carriers have been removed from the carrier list. "
            "Select carriers and click 'Restore' to add them back to the list."
        )
        description.setWordWrap(True)
        content_layout.addWidget(description)

        # Create table view
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)

        # Clear selection when clicking empty area
        self.table_view.clicked.connect(self._clear_selection_if_empty)
        content_layout.addWidget(self.table_view)

        # Add button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        # Add Restore button
        self.restore_button = QPushButton("Restore Selected")
        self.restore_button.clicked.connect(self.restore_selected_carriers)
        self.restore_button.setEnabled(False)  # Disabled until selection made
        button_layout.addWidget(self.restore_button)

        content_layout.addWidget(button_container)

        # Add content widget to main layout
        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set minimum size
        self.setMinimumSize(600, 400)

        # Load data
        self.load_removed_carriers()

        # Connect selection changed signal
        self.table_view.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )

    def load_removed_carriers(self):
        """Load removed carriers from the database."""
        try:
            with sqlite3.connect(self.eightbox_db_path) as conn:
                query = """
                    SELECT carrier_name
                    FROM ignored_carriers
                    ORDER BY carrier_name ASC
                """
                df = pd.read_sql_query(query, conn)

                # Create and set the model
                model = RemovedCarriersTableModel(df, self)
                self.table_view.setModel(model)

                # Disconnect any existing selection signals to prevent multiple connections
                try:
                    self.table_view.selectionModel().selectionChanged.disconnect()
                except (
                    TypeError
                ):  # This occurs when there are no connections to disconnect
                    pass

                # Connect selection signal to update button state
                self.table_view.selectionModel().selectionChanged.connect(
                    self.on_selection_changed
                )

                # Update button state
                self.restore_button.setEnabled(False)

        except Exception as e:
            CustomWarningDialog.warning(
                self, "Database Error", f"Failed to load removed carriers: {e}"
            )

    def restore_selected_carriers(self):
        """Remove selected carriers from the removed list and add them back to carrier list."""
        selected_rows = self.table_view.selectionModel().selectedRows()
        if not selected_rows:
            return

        # Get carrier names to restore
        model = self.table_view.model()
        carriers_to_restore = [
            model.data(model.index(row.row(), 0), Qt.DisplayRole)
            for row in selected_rows
        ]

        try:
            # First, remove from ignored list
            with sqlite3.connect(self.eightbox_db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "DELETE FROM ignored_carriers WHERE carrier_name = ?",
                    [(carrier,) for carrier in carriers_to_restore],
                )
                conn.commit()

            # Then, get carrier data from mandates database
            if self.mandates_db_path:
                try:
                    # Load current carrier list
                    current_carriers = pd.read_json(self.json_path, orient="records")
                except Exception:
                    current_carriers = pd.DataFrame(
                        columns=[
                            "carrier_name",
                            "effective_date",
                            "list_status",
                            "route_s",
                            "hour_limit",
                        ]
                    )

                # Get carrier data from mandates database
                with sqlite3.connect(self.mandates_db_path) as conn:
                    query = f"""
                        SELECT
                            carrier_name,
                            DATE(MAX(effective_date)) as effective_date,
                            list_status,
                            route_s,
                            station
                        FROM carriers
                        WHERE carrier_name IN ({','.join('?' * len(carriers_to_restore))})
                        GROUP BY carrier_name
                    """

                    df = pd.read_sql_query(query, conn, params=carriers_to_restore)

                    # Filter out carriers with "out of station"
                    df = df[
                        ~df["station"].str.contains(
                            "out of station", case=False, na=False
                        )
                    ]

                    # Drop the station column and add hour_limit
                    df = df.drop(columns=["station"])
                    df["hour_limit"] = 12.00

                    # Add new carriers to the list
                    updated_carriers = pd.concat(
                        [current_carriers, df], ignore_index=True
                    )

                    # Save updated carrier list
                    updated_carriers.to_json(self.json_path, orient="records")

                    # Emit signal to update carrier list if parent has the signal
                    if hasattr(self.parent_widget, "carrier_list_updated"):
                        self.parent_widget.carrier_list_updated.emit(updated_carriers)
                    if hasattr(self.parent_widget, "data_updated"):
                        self.parent_widget.data_updated.emit(updated_carriers)

            # Reload the removed carriers table
            self.load_removed_carriers()

            # Show success message
            message = (
                f"Successfully restored {len(carriers_to_restore)} carrier(s) "
                "and added them to the carrier list."
            )
            CustomNotificationDialog.show_notification(
                self,
                "Success",
                message,
            )

        except Exception as e:
            CustomWarningDialog.warning(
                self, "Database Error", f"Failed to restore carriers: {e}"
            )

    def on_selection_changed(self, selected, deselected):
        """Handle selection changes in the table view."""
        self.restore_button.setEnabled(
            len(self.table_view.selectionModel().selectedRows()) > 0
        )

    def _clear_selection_if_empty(self, index):
        """Clear selection if user clicks in empty area."""
        if not index.isValid():
            self.table_view.clearSelection()
            self.restore_button.setEnabled(False)
