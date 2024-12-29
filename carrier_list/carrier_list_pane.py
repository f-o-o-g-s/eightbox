"""Main carrier list management interface."""

import os

import pandas as pd
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    ConfirmDialog,
    CustomErrorDialog,
    CustomNotificationDialog,
    CustomTitleBarWidget,
)
from removed_carriers_manager import RemovedCarriersManager

from .db.carrier_db_manager import CarrierDBManager
from .models.carrier_list_proxy_model import CarrierListProxyModel
from .models.pandas_table_model import PandasTableModel
from .ui.carrier_edit_dialog import CarrierEditDialog
from .ui.carrier_stats_panel import CarrierStatsPanel
from .ui.carrier_table_view import CarrierTableView
from .ui.new_carriers_dialog import NewCarriersDialog
from .ui.styles import (
    BUTTON_CONTAINER_STYLE,
    SEARCH_BAR_STYLE,
    SEARCH_ICON_STYLE,
)


class CarrierListPane(QWidget):
    """Main widget for managing carrier list interface.

    Provides functionality for displaying, filtering, editing, and managing
    carrier information including their list status and hour limits.

    Signals:
        data_updated: Emitted when carrier data is modified
        reload_requested: Emitted when application reload is needed
        request_apply_date_range: Emitted when date range should be applied
        carrier_list_updated: Emitted when carrier list is modified
    """

    data_updated = pyqtSignal(pd.DataFrame)  # Signal to notify about data changes
    reload_requested = pyqtSignal()  # Signal to request application reload
    request_apply_date_range = pyqtSignal()  # Signal for date range application
    carrier_list_updated = pyqtSignal(pd.DataFrame)  # Signal for list updates

    def __init__(
        self,
        mandates_db_path,
        otdl_maximization_pane=None,
        fetch_clock_ring_data_callback=None,
        parent=None,
    ):
        """Initialize the carrier list pane.

        Args:
            mandates_db_path (str): Path to the mandates database
            otdl_maximization_pane (QWidget, optional): OTDL maximization pane
            fetch_clock_ring_data_callback (callable, optional): Callback for fetching data
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.parent_main = parent

        # Initialize database manager
        self.eightbox_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "eightbox.sqlite"
        )
        self.db_manager = CarrierDBManager(mandates_db_path, self.eightbox_db_path)
        self.json_path = "carrier_list.json"

        # Create ignored_carriers table if it doesn't exist
        self.db_manager.create_ignored_carriers_table()

        # Set window flags
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Initialize UI (this creates self.main_model and other UI components)
        self.setup_ui()

        # Load and pre-sort the carrier data
        df = self.load_carrier_list()
        # Create categorical type for list_status with custom order
        status_order = ["nl", "wal", "otdl", "ptf"]
        df["list_status"] = pd.Categorical(
            df["list_status"], categories=status_order, ordered=True
        )
        # Sort by list_status first, then carrier_name
        self.carrier_df = df.sort_values(
            ["list_status", "carrier_name"], ascending=[True, True]
        ).reset_index(drop=True)
        self.temp_df = self.carrier_df.copy()

        # Update the model with initial data
        self.main_model.update_data(self.carrier_df)
        self.proxy_model.invalidate()

        # Connect our own signal to refresh the view
        self.carrier_list_updated.connect(self.refresh_carrier_list)
        self.data_updated.connect(self.refresh_carrier_list)

        # Update statistics
        self.update_statistics()

    def setup_ui(self):
        """Set up the user interface."""
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title bar
        title_bar = CustomTitleBarWidget(title="Carrier List Setup", parent=self)
        main_layout.addWidget(title_bar)

        # Create content widget with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Add statistics panel
        self.stats_panel = CarrierStatsPanel(self)
        self.stats_panel.status_filter_changed.connect(self.filter_by_status)
        content_layout.addWidget(self.stats_panel)

        # Create search bar
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search carriers...")
        self.filter_input.setStyleSheet(SEARCH_BAR_STYLE)
        self.filter_input.textChanged.connect(self.apply_filter)

        # Create search icon
        search_icon = QLabel("⚲")  # Unicode search symbol
        search_icon.setStyleSheet(SEARCH_ICON_STYLE)
        search_icon.setParent(self.filter_input)
        search_icon.move(12, 8)

        search_layout.addWidget(self.filter_input)
        content_layout.addWidget(search_container)

        # Add table view
        self.table_view = CarrierTableView(self)

        # Initialize models with empty DataFrame
        empty_df = pd.DataFrame(
            columns=[
                "carrier_name",
                "effective_date",
                "list_status",
                "route_s",
                "hour_limit",
            ]
        )
        self.main_model = PandasTableModel(empty_df)
        self.proxy_model = CarrierListProxyModel(self)
        self.proxy_model.setSourceModel(self.main_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table_view.setModel(self.proxy_model)

        content_layout.addWidget(self.table_view)

        # Create button row
        button_container = QWidget()
        button_container.setStyleSheet(BUTTON_CONTAINER_STYLE)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(8, 4, 8, 4)
        button_layout.setSpacing(4)

        # Left-aligned buttons
        left_button_container = QWidget()
        left_button_layout = QHBoxLayout(left_button_container)
        left_button_layout.setContentsMargins(0, 0, 0, 0)
        left_button_layout.setSpacing(4)

        edit_button = QPushButton("EDIT")
        edit_button.setFixedWidth(60)
        edit_button.clicked.connect(self.edit_carrier)
        left_button_layout.addWidget(edit_button)

        remove_button = QPushButton("REMOVE")
        remove_button.setFixedWidth(60)
        remove_button.setObjectName("destructive")
        remove_button.clicked.connect(self.remove_carrier)
        left_button_layout.addWidget(remove_button)

        removed_button = QPushButton("REMOVED")
        removed_button.setFixedWidth(60)
        removed_button.clicked.connect(self.show_removed_carriers)
        left_button_layout.addWidget(removed_button)

        button_layout.addWidget(left_button_container)
        button_layout.addStretch()

        # Right-aligned buttons
        right_button_container = QWidget()
        right_button_layout = QHBoxLayout(right_button_container)
        right_button_layout.setContentsMargins(0, 0, 0, 0)
        right_button_layout.setSpacing(4)

        reset_button = QPushButton("RESET")
        reset_button.setFixedWidth(60)
        reset_button.clicked.connect(self.reset_carrier_list)
        right_button_layout.addWidget(reset_button)

        save_button = QPushButton("SAVE")
        save_button.setFixedWidth(60)
        save_button.setObjectName("primary")
        save_button.clicked.connect(self.save_to_json)
        right_button_layout.addWidget(save_button)

        button_layout.addWidget(right_button_container)
        content_layout.addWidget(button_container)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)

        # Set minimum size
        self.setMinimumSize(300, 700)

        # Update statistics
        self.update_statistics()

        # Connect model changes to statistics updates
        self.proxy_model.layoutChanged.connect(self.update_statistics)
        self.filter_input.textChanged.connect(self.update_statistics)

    def load_carrier_list(self):
        """Load and process carrier list data.

        Returns:
            pd.DataFrame: Processed carrier list data
        """
        # Define default columns and their types
        default_columns = {
            "carrier_name": str,
            "list_status": str,
            "route_s": str,
            "hour_limit": float,
            "effective_date": str,
        }

        # Load initial data
        if os.path.exists(self.json_path):
            try:
                df = pd.read_json(self.json_path, orient="records")
            except Exception as e:
                CustomNotificationDialog.show_notification(
                    self, "Error", f"Failed to load JSON file: {e}"
                )
                df = self.db_manager.fetch_carrier_data()
        else:
            df = self.db_manager.fetch_carrier_data()

        # Ensure all required columns exist with default values
        for col, dtype in default_columns.items():
            if col not in df.columns:
                df[col] = None if dtype == str else dtype()

        # Set default values for missing data
        df["list_status"] = df["list_status"].fillna("nl")  # Default to no-list
        df["route_s"] = df["route_s"].fillna("")
        df["hour_limit"] = df["hour_limit"].fillna(12.00)  # Default to 12.00 hours

        # Convert any 0.0 hour limits to 12.00
        df.loc[df["hour_limit"] == 0.0, "hour_limit"] = 12.00

        # Ensure datetime formatting
        df["effective_date"] = pd.to_datetime(df["effective_date"]).fillna(
            pd.Timestamp.now()
        )

        # Format the date after sorting
        df["effective_date"] = df["effective_date"].dt.strftime("%Y-%m-%d")
        df = df.reset_index(drop=True)

        # Check for new carriers
        db_data = self.db_manager.fetch_carrier_data()
        new_carriers = db_data[~db_data["carrier_name"].isin(df["carrier_name"])]
        if not new_carriers.empty:
            new_carrier_names = new_carriers["carrier_name"].tolist()
            self.show_new_carriers_dialog(new_carriers, new_carrier_names, df)

        return df

    def update_statistics(self):
        """Update the carrier statistics display."""
        if self.proxy_model and self.proxy_model.sourceModel():
            # Get counts from the full dataset
            full_df = self.main_model.df
            total_carriers = len(full_df)
            otdl_total = len(full_df[full_df["list_status"] == "otdl"])
            wal_total = len(full_df[full_df["list_status"] == "wal"])
            nl_total = len(full_df[full_df["list_status"] == "nl"])
            ptf_total = len(full_df[full_df["list_status"] == "ptf"])

            # Update the stats panel
            self.stats_panel.update_stats(
                total_carriers, otdl_total, wal_total, nl_total, ptf_total
            )

    def filter_by_status(self, status):
        """Filter carriers by list status.

        Args:
            status (str): Status to filter by ('all', 'otdl', 'wal', 'nl', 'ptf')
        """
        self.filter_input.clear()
        self.proxy_model.set_status_filter(status)
        self.update_statistics()

    def apply_filter(self, text):
        """Apply text filter to carrier list.

        Args:
            text (str): Text to filter by
        """
        self.proxy_model.set_text_filter(text)
        self.update_statistics()

    def edit_carrier(self):
        """Edit the selected carrier's details."""
        selected_index = self.table_view.currentIndex()
        if not selected_index.isValid():
            CustomNotificationDialog.show_notification(
                self, "No Selection", "Please select a carrier to edit."
            )
            return

        # Map the selected index back to the DataFrame index
        source_index = self.proxy_model.mapToSource(selected_index)
        row = source_index.row()

        # Get the correct row index in the sorted DataFrame
        sorted_df_index = self.main_model.df.index[row]

        # Fetch existing values for the carrier
        carrier_data = self.main_model.df.loc[sorted_df_index].to_dict()

        # Show edit dialog
        dialog = CarrierEditDialog(carrier_data, self)
        if dialog.exec_():
            updated_data = dialog.get_updated_data()
            if updated_data:
                # Update the DataFrame
                for key, value in updated_data.items():
                    self.main_model.df.loc[sorted_df_index, key] = value

                # Refresh the view
                self.main_model.update_data(self.main_model.df)
                self.proxy_model.invalidate()

    def remove_carrier(self):
        """Remove the selected carrier from the list."""
        try:
            selected_index = self.table_view.selectionModel().currentIndex()
            if not selected_index.isValid():
                CustomNotificationDialog.show_notification(
                    self, "No Selection", "Please select a carrier to remove."
                )
                return

            # Map the selected index to the source model
            source_index = self.proxy_model.mapToSource(selected_index)
            row = source_index.row()

            # Get the correct row index in the sorted DataFrame
            sorted_df_index = self.main_model.df.index[row]

            # Fetch the carrier name using the correct index
            carrier_name = self.main_model.df.loc[sorted_df_index, "carrier_name"]

            # Show confirmation dialog
            confirm_dialog = ConfirmDialog(
                f"Are you sure you want to remove carrier '{carrier_name}'?\n\n"
                "The carrier will be added to the removed list\n\n"
                "and won't appear in violation detection.",
                self,
            )
            if confirm_dialog.exec_():
                # Add carrier to ignored list
                self.db_manager.add_to_ignored_carriers([carrier_name])

                # Drop the row from the DataFrame
                self.main_model.df.drop(index=sorted_df_index, inplace=True)
                self.main_model.df.reset_index(drop=True, inplace=True)

                # Update the JSON file
                try:
                    self.main_model.df.to_json(self.json_path, orient="records")
                except Exception as e:
                    CustomErrorDialog.error(
                        self, "Error", f"Failed to update the JSON file: {e}"
                    )
                    return

                # Update the table view
                self.main_model.update_data(self.main_model.df)

                # Emit the signal when data is updated
                self.data_updated.emit(self.main_model.df)

                CustomNotificationDialog.show_notification(
                    self,
                    "Success",
                    f"Carrier '{carrier_name}' removed successfully and added to ignored list.",
                )

                # Clear the selection after removal
                self.table_view.clearSelection()

        except Exception as e:
            CustomErrorDialog.error(
                self, "Error", f"An error occurred while removing the carrier: {e}"
            )
            # Ensure the UI is in a good state
            self.table_view.clearSelection()

    def show_removed_carriers(self):
        """Show the removed carriers manager dialog."""
        dialog = RemovedCarriersManager(self.eightbox_db_path, parent=self)
        dialog.exec_()
        # Force a refresh after dialog closes
        try:
            updated_df = pd.read_json(self.json_path, orient="records")
            self.refresh_carrier_list(updated_df)
        except Exception as e:
            CustomErrorDialog.error(
                self, "Error", f"Failed to refresh carrier list after restore: {e}"
            )

    def reset_carrier_list(self):
        """Reset the carrier list to its initial state."""
        confirm_dialog = ConfirmDialog(
            "Are you sure you want to reset the carrier list?\n\n"
            "This will remove all customizations and reload carriers from the database.",
            self,
        )
        if confirm_dialog.exec_():
            try:
                # Delete the JSON file if it exists
                if os.path.exists(self.json_path):
                    os.remove(self.json_path)

                # Reload carrier data from database
                df = self.db_manager.fetch_carrier_data()

                # Update the model with the new data
                self.main_model.update_data(df)

                # Emit signals to update the main application
                self.carrier_list_updated.emit(df)
                self.data_updated.emit(df)

                # If we have a valid date selected, trigger a refresh
                if self.has_valid_date_range():
                    self.request_apply_date_range.emit()

                CustomNotificationDialog.show_notification(
                    self, "Success", "Carrier list has been reset to its initial state."
                )

                # Update statistics
                self.update_statistics()

            except Exception as e:
                CustomErrorDialog.error(
                    self, "Error", f"Failed to reset carrier list: {e}"
                )

    def save_to_json(self):
        """Save the current carrier list to JSON file."""
        try:
            self.main_model.df.to_json(self.json_path, orient="records")
            CustomNotificationDialog.show_notification(
                self, "Success", "Carrier list has been saved."
            )

            # Check if date selection pane exists and has a date selected
            if self.has_valid_date_range():
                # Only emit signals if we have a valid date range
                self.carrier_list_updated.emit(self.main_model.df)
                self.request_apply_date_range.emit()
            else:
                CustomNotificationDialog.show_notification(
                    self,
                    "Note",
                    "Carrier list saved. Select a date range to view updated violations.",
                )

        except Exception as e:
            CustomNotificationDialog.show_notification(
                self, "Error", f"Failed to save carrier list: {e}"
            )

    def has_valid_date_range(self):
        """Check if a valid date range is selected.

        Returns:
            bool: True if a valid date range is selected, False otherwise
        """
        return (
            hasattr(self.parent_widget, "date_selection_pane")
            and self.parent_widget.date_selection_pane is not None
            and hasattr(self.parent_widget.date_selection_pane, "selected_range")
            and self.parent_widget.date_selection_pane.selected_range is not None
        )

    def refresh_carrier_list(self, updated_df=None):
        """Refresh the carrier list view with updated data.

        Args:
            updated_df (pd.DataFrame, optional): Updated carrier data
        """
        try:
            if updated_df is None:
                # Reload from JSON file
                updated_df = pd.read_json(self.json_path, orient="records")

            # Sort the DataFrame
            status_order = ["nl", "wal", "otdl", "ptf"]
            updated_df["list_status"] = pd.Categorical(
                updated_df["list_status"], categories=status_order, ordered=True
            )
            updated_df = updated_df.sort_values(
                ["list_status", "carrier_name"], ascending=[True, True]
            ).reset_index(drop=True)

            # Update the model
            self.carrier_df = updated_df
            self.main_model.update_data(updated_df)
            self.proxy_model.invalidate()

            # Update statistics
            self.update_statistics()

        except Exception as e:
            CustomErrorDialog.error(
                self, "Error", f"Failed to refresh carrier list: {e}"
            )

    def hideEvent(self, event):
        """Handle hide event by unchecking the corresponding button."""
        if hasattr(self.parent_main, "carrier_list_button"):
            self.parent_main.carrier_list_button.setChecked(False)
        super().hideEvent(event)

    def show_new_carriers_dialog(self, new_carriers, new_carrier_names, df):
        """Display dialog for handling newly discovered carriers.

        Shows a dialog allowing user to select which new carriers to add
        to the list and handles updating the data accordingly.

        Args:
            new_carriers (pd.DataFrame): DataFrame containing new carrier data
            new_carrier_names (list): List of new carrier names
            df (pd.DataFrame): Current carrier list DataFrame
        """
        # Filter out ignored carriers
        ignored_carriers = self.db_manager.get_ignored_carriers()
        new_carrier_names = [
            name for name in new_carrier_names if name not in ignored_carriers
        ]

        if not new_carrier_names:
            return

        # Show custom dialog and get selected carriers
        selected_carriers, carriers_to_ignore = NewCarriersDialog.get_new_carriers(
            self.parent_widget, new_carrier_names
        )

        # Add selected carriers to ignored list
        if carriers_to_ignore:
            self.db_manager.add_to_ignored_carriers(carriers_to_ignore)

        if selected_carriers:
            # Add selected carriers to the DataFrame
            selected_data = new_carriers[
                new_carriers["carrier_name"].isin(selected_carriers)
            ]
            updated_df = pd.concat([df, selected_data], ignore_index=True)

            # Update the model with the new data
            self.main_model.update_data(updated_df)

            # Save the updated list to JSON immediately
            try:
                updated_df.to_json(self.json_path, orient="records")

                # Emit signals to update the main application
                self.carrier_list_updated.emit(updated_df)
                self.data_updated.emit(updated_df)

                # If we have a valid date selected, trigger a refresh
                if (
                    hasattr(self.parent_widget, "date_selection_pane")
                    and self.parent_widget.date_selection_pane is not None
                    and self.parent_widget.date_selection_pane.selected_range
                    is not None
                ):
                    self.request_apply_date_range.emit()

            except Exception as e:
                CustomErrorDialog.error(
                    self, "Error", f"Failed to save updated carrier list: {e}"
                )
                return

            CustomNotificationDialog.show_notification(
                self,
                "Success",
                f"{len(selected_carriers)} carriers have been added to the list. "
                "Please open the Carrier List to review your changes.",
            )

            # Update statistics
            self.update_statistics()
