"""Custom widget implementations for the application's user interface.

Contains specialized widgets and UI components that extend PyQt's base widgets
with additional functionality specific to the application's needs.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from theme import (
    CLOSE_BUTTON_STYLE,
    CONFIRM_DIALOG_STYLE,
    CUSTOM_INFO_DIALOG_STYLE,
    CUSTOM_MESSAGE_BOX_STYLE,
    CUSTOM_NOTIFICATION_DIALOG_STYLE,
    CUSTOM_PROGRESS_DIALOG_STYLE,
    CUSTOM_TITLE_BAR_STYLE,
    CUSTOM_WARNING_DIALOG_STYLE,
    MATERIAL_GREY_600,
    MATERIAL_GREY_700,
    NEW_CARRIERS_DIALOG_STYLE,
)

# Base64 encoded checkmark icon
CHECKMARK_BASE64 = (
    "PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Im"
    "h0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w0LjUgOC41TDIgNiIgc3Ryb2tlPSJ3aGl0"
    "ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz"
    "48L3N2Zz4="
)


class CustomTitleBarWidget(QWidget):
    """Custom title bar widget that replaces the default window title bar.

    Provides a custom-styled title bar with minimize and close buttons.
    Supports window dragging functionality.

    Args:
        title (str): Text to display in the title bar
        parent (QWidget): Parent widget, typically the main window
    """

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.drag_pos = None

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_label = QLabel(f"  {title}")
        layout.addWidget(title_label)
        layout.addStretch()

        window_controls = QWidget()
        window_controls_layout = QHBoxLayout()
        window_controls_layout.setContentsMargins(0, 0, 0, 0)
        window_controls_layout.setSpacing(0)

        minimize_btn = QPushButton("─")
        minimize_btn.clicked.connect(self.handle_minimize)

        close_btn = QPushButton("×")
        close_btn.setStyleSheet(CLOSE_BUTTON_STYLE)
        close_btn.clicked.connect(self.handle_close)

        window_controls_layout.addWidget(minimize_btn)
        window_controls_layout.addWidget(close_btn)
        window_controls.setLayout(window_controls_layout)

        layout.addWidget(window_controls)
        self.setLayout(layout)

        self.setStyleSheet(CUSTOM_TITLE_BAR_STYLE)

    def handle_minimize(self):
        """Handle minimize button click by unchecking the corresponding button in main window."""
        if hasattr(self.parent, "parent_main"):
            main_window = self.parent.parent_main
            if "Date Selection" in self.parent.windowTitle() and hasattr(
                main_window, "date_selection_button"
            ):
                main_window.date_selection_button.setChecked(False)
            elif "Carrier List" in self.parent.windowTitle() and hasattr(
                main_window, "carrier_list_button"
            ):
                main_window.carrier_list_button.setChecked(False)
            elif "OTDL Maximization" in self.parent.windowTitle() and hasattr(
                main_window, "otdl_maximization_button"
            ):
                main_window.otdl_maximization_button.setChecked(False)
        self.parent.hide()

    def handle_close(self):
        """Handle close button click by unchecking the corresponding button in main window."""
        if hasattr(self.parent, "parent_main"):
            main_window = self.parent.parent_main
            if "Date Selection" in self.parent.windowTitle() and hasattr(
                main_window, "date_selection_button"
            ):
                main_window.date_selection_button.setChecked(False)
            elif "Carrier List" in self.parent.windowTitle() and hasattr(
                main_window, "carrier_list_button"
            ):
                main_window.carrier_list_button.setChecked(False)
            elif "OTDL Maximization" in self.parent.windowTitle() and hasattr(
                main_window, "otdl_maximization_button"
            ):
                main_window.otdl_maximization_button.setChecked(False)
        self.parent.hide()

    def mouse_press_event(self, event):
        """Handle mouse press events for window dragging.

        Args:
            event (QMouseEvent): The mouse event
        """
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouse_move_event(self, event):
        """Handle mouse move events for window dragging.

        Args:
            event (QMouseEvent): The mouse event
        """
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.parent.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouse_release_event(self, event):
        """Handle mouse release events for window dragging.

        Args:
            event (QMouseEvent): The mouse event
        """
        if event.button() == Qt.LeftButton:
            self.drag_pos = None
            event.accept()

    # Alias Qt method names to maintain compatibility
    mousePressEvent = mouse_press_event
    mouseMoveEvent = mouse_move_event
    mouseReleaseEvent = mouse_release_event


class CustomProgressDialog(QProgressDialog):
    """Custom progress dialog with Material Design styling.

    Provides a progress dialog with custom title bar and styling that matches
    the application's theme. Supports progress updates and cancel functionality.

    Args:
        label_text (str): Text describing the operation in progress
        cancel_button_text (str): Text for the cancel button. If None, no cancel button is shown.
        minimum (int): Minimum progress value
        maximum (int): Maximum progress value
        parent (QWidget): Parent widget
        title (str, optional): Dialog title. Defaults to "Progress"
    """

    def __init__(
        self,
        label_text,
        cancel_button_text,
        minimum,
        maximum,
        parent=None,
        title="Progress",
    ):
        super().__init__(label_text, cancel_button_text, minimum, maximum, parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.canceled = False

        # Create custom title bar with passed title
        self.title_bar = CustomTitleBarWidget(title, self)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add title bar
        layout.addWidget(self.title_bar)

        # Create content widget with dark background
        content_widget = QWidget()
        content_widget.setStyleSheet(CUSTOM_PROGRESS_DIALOG_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(8)

        # Create a container for progress elements with minimum width
        progress_container = QWidget()
        progress_container.setMinimumWidth(300)  # Set minimum width instead of fixed
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        # Move the progress bar and label to our custom layout
        progress_bar = self.findChild(QProgressBar)
        label = self.findChild(QLabel)

        if progress_bar and label:
            progress_layout.addWidget(label)
            progress_layout.addWidget(progress_bar)

        # Create cancel button if text is provided
        if cancel_button_text:
            self.cancel_button = QPushButton(cancel_button_text)
            self.cancel_button.clicked.connect(self.handle_cancel)
            progress_layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        else:
            self.cancel_button = None

        # Add the progress container to the content layout
        content_layout.addWidget(progress_container, alignment=Qt.AlignCenter)
        layout.addWidget(content_widget)

        # Set the layout directly on the QProgressDialog
        self.setLayout(layout)

        # Adjust size after layout is set
        self.adjustSize()

        # Center the dialog on the parent
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )

    def handle_cancel(self):
        """Handle cancel button click."""
        self.canceled = True
        self.cancel()

    def was_canceled(self):
        """Check if the operation was canceled.

        Returns:
            bool: True if the operation was canceled, False otherwise
        """
        return self.canceled


class CustomMessageBox(QWidget):
    """Custom message box with Material Design styling.

    Provides a simple message dialog with an OK button and custom styling
    that matches the application's theme.

    Args:
        title (str): Dialog title
        message (str): Message to display
        parent (QWidget): Parent widget
    """

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(title, self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(CUSTOM_MESSAGE_BOX_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Add message label
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label)

        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        content_layout.addWidget(ok_button, alignment=Qt.AlignCenter)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set fixed size
        self.setFixedSize(400, 150)

        # Center on parent
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )


class CustomWarningDialog(QDialog):
    """Custom warning dialog with Material Design styling.

    Provides a warning dialog with Yes/No buttons and custom styling.
    Includes a warning icon and supports user choice confirmation.

    Args:
        title (str): Dialog title
        message (str): Warning message to display
        parent (QWidget): Parent widget
    """

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.result = QMessageBox.No

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(title, self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(CUSTOM_WARNING_DIALOG_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Warning icon and message layout
        message_layout = QHBoxLayout()

        # Warning icon
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style().standardIcon(self.style().SP_MessageBoxWarning).pixmap(32, 32)
        )
        icon_label.setFixedSize(32, 32)  # Icons can stay fixed size
        message_layout.addWidget(icon_label, 0)  # 0 means don't stretch

        # Message text - now more flexible
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(300)  # Minimum width for readability
        message_layout.addWidget(message_label, 1)  # 1 means stretch to fill space

        content_layout.addLayout(message_layout)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")

        yes_button.clicked.connect(self.accept)
        no_button.clicked.connect(self.reject)

        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)

        content_layout.addLayout(button_layout)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Instead of fixed size, set minimum size for usability
        self.setMinimumSize(400, 180)

        # Let the dialog size itself based on content
        self.adjustSize()

        # Center on parent
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )

    def accept(self):
        """Accept the warning dialog and set result to Yes.

        Overrides the QDialog accept() method to track the user's choice
        before closing the dialog.

        Note:
            - Sets self.result to QMessageBox.Yes
            - Calls parent class accept() to close dialog
            - Used by the 'Yes' button click handler
        """
        self.result = QMessageBox.Yes
        super().accept()

    def reject(self):
        """Reject the warning dialog and set result to No.

        Overrides the QDialog reject() method to track the user's choice
        before closing the dialog.

        Note:
            - Sets self.result to QMessageBox.No
            - Calls parent class reject() to close dialog
            - Used by both 'No' button and close button
        """
        self.result = QMessageBox.No
        super().reject()

    @staticmethod
    def warning(parent, title, message):
        """Show a warning dialog and return the user's choice.

        Args:
            parent (QWidget): Parent widget
            title (str): Dialog title
            message (str): Warning message to display

        Returns:
            QMessageBox.StandardButton: QMessageBox.Yes or QMessageBox.No
        """
        dialog = CustomWarningDialog(title, message, parent)
        dialog.exec_()
        return dialog.result


class CustomInfoDialog(QDialog):
    """Custom dialog for displaying information messages.

    A themed dialog that displays information messages with an icon
    and formatted text. Uses the custom title bar and themed styling.
    """

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(title, self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(CUSTOM_INFO_DIALOG_STYLE)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(
            36, 24, 24, 24
        )  # Increased left margin to 36px

        # Create horizontal layout for icon and text
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Create fixed-width container for icon
        icon_container = QWidget()
        icon_container.setFixedWidth(40)  # Fixed width container
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)

        # Info icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(
            self.style()
            .standardIcon(self.style().SP_MessageBoxInformation)
            .pixmap(32, 32)
        )
        self.icon_label.setFixedSize(32, 32)
        icon_layout.addWidget(self.icon_label, 0, Qt.AlignLeft)

        info_layout.addWidget(icon_container)

        # Message text with HTML formatting
        self.message_label = QLabel()
        self.message_label.setTextFormat(Qt.RichText)
        self.message_label.setText(message)
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumWidth(300)
        info_layout.addWidget(self.message_label, 1)

        content_layout.addLayout(info_layout)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        button_layout.addWidget(ok_button)

        content_layout.addLayout(button_layout)
        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set minimum size for usability
        self.setMinimumSize(450, 180)

        # Let the dialog size itself based on content
        self.adjustSize()

        # Center on parent
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )

    @staticmethod
    def information(parent, title, message):
        """Show an information dialog.

        Args:
            parent (QWidget): Parent widget
            title (str): Dialog title
            message (str): Information message to display (supports HTML)
        """
        dialog = CustomInfoDialog(title, message, parent)
        dialog.exec_()


class CustomNotificationDialog(QDialog):
    """Custom notification dialog with Material Design styling.

    Provides a notification dialog that appears centered on the parent window
    or screen. Includes an information icon and OK button.

    Args:
        title (str): Dialog title
        message (str): Notification message to display
        parent (QWidget): Parent widget
    """

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget(title, self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(CUSTOM_NOTIFICATION_DIALOG_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Message layout
        message_layout = QHBoxLayout()

        # Info icon
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style()
            .standardIcon(self.style().SP_MessageBoxInformation)
            .pixmap(32, 32)
        )
        icon_label.setFixedSize(32, 32)
        message_layout.addWidget(icon_label, 0)

        # Message text
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(200)
        message_layout.addWidget(message_label, 1)

        content_layout.addLayout(message_layout)

        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        content_layout.addLayout(button_layout)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set minimum size and adjust based on content
        self.setMinimumSize(300, 150)
        self.adjustSize()

        # Center on parent
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )

    @staticmethod
    def show_notification(parent, title, message):
        """Show a notification dialog centered on the parent window.

        Args:
            parent (QWidget): Parent widget
            title (str): Dialog title
            message (str): Notification message to display
        """
        dialog = CustomNotificationDialog(title, message, parent)

        # Center the notification on the parent window
        if parent and parent.isVisible():
            parent_geo = parent.geometry()
            dialog_geo = dialog.geometry()
            x = parent_geo.x() + (parent_geo.width() - dialog_geo.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - dialog_geo.height()) // 2
            dialog.move(x, y)
        else:
            # Center on screen if no parent
            screen = QApplication.primaryScreen().geometry()
            dialog_geo = dialog.geometry()
            x = (screen.width() - dialog_geo.width()) // 2
            y = (screen.height() - dialog_geo.height()) // 2
            dialog.move(x, y)

        dialog.exec_()


class CustomErrorDialog(QDialog):
    """Custom error dialog with Material Design styling.

    Provides an error dialog with an OK button and custom styling.
    Includes an error icon and displays error messages in a user-friendly format.

    Args:
        title (str): Dialog title
        message (str): Error message to display
        parent (QWidget): Parent widget
    """

    @staticmethod
    def error(parent, title, message):
        """Show an error dialog and return the result.

        Args:
            parent (QWidget): Parent widget
            title (str): Dialog title
            message (str): Error message to display

        Returns:
            int: Dialog execution result code
        """


class ConfirmDialog(QDialog):
    """Custom confirmation dialog with Material Design styling.

    Provides a confirmation dialog with Yes/No buttons and custom styling.
    Includes a question icon and is typically used for confirming destructive actions.

    Args:
        message (str): Confirmation message to display
        parent (QWidget): Parent widget
    """

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("Confirm Removal", self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(CONFIRM_DIALOG_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Question icon and message layout
        message_layout = QHBoxLayout()

        # Question icon
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style().standardIcon(self.style().SP_MessageBoxQuestion).pixmap(32, 32)
        )
        icon_label.setFixedSize(32, 32)
        message_layout.addWidget(icon_label, 0)

        # Message text
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(300)
        message_layout.addWidget(message_label, 1)

        content_layout.addLayout(message_layout)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")

        yes_button.clicked.connect(self.accept)
        no_button.clicked.connect(self.reject)

        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)

        content_layout.addLayout(button_layout)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set minimum size and adjust based on content
        self.setMinimumSize(400, 150)
        self.adjustSize()

        # Center on parent
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2,
            )


class NewCarriersDialog(QDialog):
    """Dialog for selecting new carriers to add to the list.

    Displays a list of newly detected carriers and allows the user to
    select which ones to add to the carrier list.
    """

    @staticmethod
    def get_new_carriers(parent, carrier_names):
        """Show dialog for selecting new carriers to add.

        Args:
            parent: Parent widget
            carrier_names (list): List of new carrier names

        Returns:
            tuple: (selected_carriers, []) - List of selected carriers
            and empty list for compatibility
        """
        dialog = NewCarriersDialog(parent, carrier_names)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_selected_carriers(), []
        return [], []

    def __init__(self, parent, carrier_names):
        """Initialize the dialog.

        Args:
            parent: Parent widget
            carrier_names (list): List of new carrier names
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        title_bar = CustomTitleBarWidget("New Carriers Detected", self)
        layout.addWidget(title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(NEW_CARRIERS_DIALOG_STYLE)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Add description label
        description = QLabel("Select the new carriers to add to the carrier list:")
        description.setWordWrap(True)
        content_layout.addWidget(description)

        # Add checkboxes for carriers
        self.carrier_checkboxes = {}
        for carrier in carrier_names:
            checkbox = QCheckBox(carrier)
            checkbox.setChecked(True)  # Default to checked
            self.carrier_checkboxes[carrier] = checkbox
            content_layout.addWidget(checkbox)

        # Add button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        # Add Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondary")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        content_layout.addWidget(button_container)

        # Add content widget to main layout
        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set minimum size
        self.setMinimumSize(300, 200)

    def get_selected_carriers(self):
        """Get the list of selected carriers.

        Returns:
            list: Names of selected carriers
        """
        return [
            carrier
            for carrier, checkbox in self.carrier_checkboxes.items()
            if checkbox.isChecked()
        ]


class CustomSizeGrip(QSizeGrip):
    """Custom size grip widget with classic Windows-style diagonal dots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)

    def paint_event(self, event):
        """Paint the classic diagonal dot pattern."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Use theme colors
        dot_color = MATERIAL_GREY_600
        hover_color = MATERIAL_GREY_700

        # Use hover color if mouse is over the grip
        if self.underMouse():
            painter.setBrush(hover_color)
        else:
            painter.setBrush(dot_color)

        painter.setPen(Qt.NoPen)

        # Draw dots in a diagonal pattern
        dot_size = 2
        spacing = 4

        # Start from bottom-right corner, going up and left
        for i in range(4):  # Number of rows
            for j in range(4 - i):  # Dots in each row, decreasing as we go up
                x = self.width() - (4 - i) * spacing + j * spacing
                y = self.height() - (i + 1) * spacing
                painter.drawEllipse(x, y, dot_size, dot_size)

    # Alias Qt method name to maintain compatibility
    paintEvent = paint_event


# Make sure these classes are available for import
__all__ = [
    "CustomTitleBarWidget",
    "CustomProgressDialog",
    "CustomMessageBox",
    "CustomNotificationDialog",
    "CustomWarningDialog",
    "CustomInfoDialog",
    "CustomErrorDialog",
    "ConfirmDialog",
    "NewCarriersDialog",
    "CustomSizeGrip",
]
