"""Dialog for editing carrier information."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import CustomTitleBarWidget

from ..ui.styles import EDIT_DIALOG_STYLE


class CarrierEditDialog(QDialog):
    """Dialog for editing carrier information.

    Provides a form for modifying carrier list status and hour limits.
    """

    def __init__(self, carrier_data, parent=None):
        """Initialize the edit dialog.

        Args:
            carrier_data (dict): Current carrier data to edit
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.carrier_data = carrier_data
        self.result_data = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog's user interface."""
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout with no margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        title_bar = CustomTitleBarWidget(title="Edit Carrier", parent=self)
        main_layout.addWidget(title_bar)

        # Create content widget with Material Design styling
        content_widget = QWidget()
        content_widget.setStyleSheet(EDIT_DIALOG_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(8)

        # Add a title label
        title_label = QLabel(f"Editing Carrier: {self.carrier_data['carrier_name']}")
        title_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            padding: 0px 0px 16px 0px;
            """
        )
        content_layout.addWidget(title_label)

        # Carrier name input with icon
        name_label = QLabel("Carrier Name")
        self.name_input = QLineEdit(self.carrier_data["carrier_name"])
        self.name_input.setReadOnly(True)
        content_layout.addWidget(name_label)
        content_layout.addWidget(self.name_input)

        # List status dropdown with icon
        list_status_label = QLabel("List Status")
        self.list_status_dropdown = QComboBox()
        self.list_status_dropdown.addItems(["otdl", "ptf", "wal", "nl"])
        self.list_status_dropdown.setCurrentText(self.carrier_data["list_status"])
        content_layout.addWidget(list_status_label)
        content_layout.addWidget(self.list_status_dropdown)

        # Hour limit dropdown with icon
        hour_limit_label = QLabel("Hour Limit")
        self.hour_limit_dropdown = QComboBox()
        content_layout.addWidget(hour_limit_label)
        content_layout.addWidget(self.hour_limit_dropdown)

        # Update hour limit options based on list status
        self.update_hour_limit_options()
        self.list_status_dropdown.currentTextChanged.connect(
            self.update_hour_limit_options
        )

        # Set current hour limit
        current_hour_limit = self.carrier_data["hour_limit"]
        if current_hour_limit is not None:
            try:
                current_hour_limit = f"{float(current_hour_limit):.2f}"
            except (ValueError, TypeError):
                current_hour_limit = "(none)"
        else:
            current_hour_limit = "(none)"

        if current_hour_limit in [
            self.hour_limit_dropdown.itemText(i)
            for i in range(self.hour_limit_dropdown.count())
        ]:
            self.hour_limit_dropdown.setCurrentText(current_hour_limit)
        else:
            self.hour_limit_dropdown.setCurrentText("(none)")

        # Add spacing before buttons
        content_layout.addSpacing(16)

        # Create button container with horizontal layout
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(16)
        button_layout.addStretch()

        # Create OK and Cancel buttons
        ok_button = QPushButton("Save")
        ok_button.setObjectName("primary")
        cancel_button = QPushButton("Cancel")

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        content_layout.addWidget(button_container)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)

        # Set minimum size and center on parent
        self.setMinimumSize(400, 500)
        if self.parent():
            self.move(
                self.parent().x() + (self.parent().width() - self.width()) // 2,
                self.parent().y() + (self.parent().height() - self.height()) // 2,
            )

        # Connect buttons
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def update_hour_limit_options(self):
        """Update hour limit options based on selected list status."""
        self.hour_limit_dropdown.clear()
        if self.list_status_dropdown.currentText().lower() == "otdl":
            self.hour_limit_dropdown.addItems(["12.00", "11.00", "10.00"])
        else:
            self.hour_limit_dropdown.addItems(["12.00", "11.00", "10.00", "(none)"])

    def get_updated_data(self):
        """Get the updated carrier data.

        Returns:
            dict: Updated carrier data with new list status and hour limit
        """
        if self.result() == QDialog.Accepted:
            selected_hour_limit = self.hour_limit_dropdown.currentText()
            return {
                "list_status": self.list_status_dropdown.currentText(),
                "hour_limit": None
                if selected_hour_limit == "(none)"
                else float(selected_hour_limit),
            }
        return None
