"""Dialog for handling newly discovered carriers."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import CustomTitleBarWidget


class NewCarriersDialog(QDialog):
    """Dialog for selecting which new carriers to add to the list."""

    @staticmethod
    def get_new_carriers(parent, carrier_names):
        """Show dialog and get selected carriers.

        Args:
            parent (QWidget): Parent widget
            carrier_names (list): List of new carrier names

        Returns:
            tuple: (selected_carriers, carriers_to_ignore)
        """
        dialog = NewCarriersDialog(parent, carrier_names)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            return dialog.get_selected_carriers(), dialog.get_carriers_to_ignore()
        return [], []

    def __init__(self, parent, carrier_names):
        """Initialize the dialog.

        Args:
            parent (QWidget): Parent widget
            carrier_names (list): List of new carrier names
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.carrier_names = carrier_names
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title bar
        title_bar = CustomTitleBarWidget(title="New Carriers Found", parent=self)
        main_layout.addWidget(title_bar)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # Add description label
        description = QLabel(
            "New carriers have been found in the clock rings.\n"
            "Select which carriers you want to add to your list:"
        )
        description.setWordWrap(True)
        content_layout.addWidget(description)

        # Add list widget
        self.list_widget = QListWidget()
        self.list_widget.addItems(self.carrier_names)
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        content_layout.addWidget(self.list_widget)

        # Add buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)

        content_layout.addWidget(button_container)

        # Add action buttons
        action_container = QWidget()
        action_layout = QHBoxLayout(action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)

        ignore_btn = QPushButton("Ignore Selected")
        ignore_btn.clicked.connect(self.ignore_selected)
        action_layout.addWidget(ignore_btn)

        add_btn = QPushButton("Add Selected")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self.accept)
        action_layout.addWidget(add_btn)

        content_layout.addWidget(action_container)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)

        # Set minimum size
        self.setMinimumSize(400, 500)

    def select_all(self):
        """Select all carriers in the list."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(True)

    def deselect_all(self):
        """Deselect all carriers in the list."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(False)

    def get_selected_carriers(self):
        """Get list of selected carriers.

        Returns:
            list: Names of selected carriers
        """
        return [item.text() for item in self.list_widget.selectedItems()]

    def get_carriers_to_ignore(self):
        """Get list of carriers to ignore.

        Returns:
            list: Names of carriers to ignore
        """
        selected = self.get_selected_carriers()
        return [name for name in self.carrier_names if name not in selected]

    def ignore_selected(self):
        """Handle ignoring selected carriers."""
        self.accept()
        # Return empty selected list to indicate all should be ignored
        self.list_widget.clearSelection()
