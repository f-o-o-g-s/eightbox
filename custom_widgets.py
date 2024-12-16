"""Custom widget implementations for the application's user interface.

Contains specialized widgets and UI components that extend PyQt's base widgets
with additional functionality specific to the application's needs.
"""

# Create a new file: custom_widgets.py
from PyQt5.QtCore import (
    QByteArray,
    Qt,
    QTimer,
)
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPixmap,
)
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

CHECKMARK_ICON = """
iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA
B3RJTUUH4QgPDRknF/OPiQAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUH
AAAAhUlEQVQoz62RMQ7CMAxF30/UhQk2RqZyhB4Bwd5D9Ai9UY/AwFRGJgYWJKeqVFVVBYnYbFmW
n/5vGzyJme0B4JxbhhCOvfeXlNJt7KwBQkRkZ2ZrEZkD1xjjKed8rLWu+nPe+wUwE5E9cAaOIYTT
0Gm0OQPvVc65ZQjh2Hu/pJRuY+cbMh1wQZTz4KoAAAAASUVORK5CYII=
"""


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
        minimize_btn.clicked.connect(self.parent.hide)

        close_btn = QPushButton("×")
        close_btn.setStyleSheet("QPushButton:hover { background-color: #c42b1c; }")
        close_btn.clicked.connect(self.parent.hide)

        window_controls_layout.addWidget(minimize_btn)
        window_controls_layout.addWidget(close_btn)
        window_controls.setLayout(window_controls_layout)

        layout.addWidget(window_controls)
        self.setLayout(layout)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #37474F;
                border: none;
            }
            QLabel {
                color: white;
                font-size: 12pt;
                font-weight: bold;
                background-color: transparent;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                padding: 5px;
                min-width: 40px;
                max-width: 40px;
                font-size: 16pt;
                font-family: Arial;
            }
            QPushButton:hover { background-color: #455A64; }
        """
        )

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
        cancel_button_text (str): Text for the cancel button
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
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                color: white;
            }
            QProgressBar {
                border: 1px solid #37474F;
                border-radius: 2px;
                text-align: center;
                background-color: #2D2D2D;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #9575CD;
                border-radius: 1px;
            }
            QLabel {
                color: white;
                font-size: 11px;
                margin-bottom: 5px;
            }
        """
        )

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
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 11px;
            }
            QPushButton {
                background-color: #9575CD;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
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

        # Add custom title bar (this can stay fixed height as it's a standard UI element)
        self.title_bar = CustomTitleBarWidget(title, self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
        """
        )

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
    """Custom information dialog with Material Design styling.

    Provides an information dialog with an OK button and custom styling.
    Includes an information icon and supports HTML-formatted messages.

    Args:
        title (str): Dialog title
        message (str): Information message to display (supports HTML)
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
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
        """
        )

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Info icon and message layout
        message_layout = QHBoxLayout()

        # Info icon
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style()
            .standardIcon(self.style().SP_MessageBoxInformation)
            .pixmap(32, 32)
        )
        icon_label.setFixedSize(32, 32)  # Icons can stay fixed size
        message_layout.addWidget(icon_label, 0)  # 0 means don't stretch

        # Message text with HTML formatting - now more flexible
        message_label = QLabel()
        message_label.setTextFormat(Qt.RichText)
        message_label.setText(message)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(300)  # Minimum width for readability
        message_layout.addWidget(message_label, 1)  # 1 for stretch factor

        content_layout.addLayout(message_layout)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        button_layout.addWidget(ok_button)

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
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
        """
        )

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
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
        """
        )

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
    """Custom dialog for selecting new carriers to add.

    Provides a dialog with checkboxes for selecting multiple carriers from a list.
    Features Material Design styling and custom checkmark icons.

    Args:
        carriers (list): List of carrier names to display
        parent (QWidget): Parent widget

    Attributes:
        checkboxes (dict): Dictionary mapping carrier names to their checkboxes
    """

    def __init__(self, carriers, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Create the checkmark icon
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray.fromBase64(CHECKMARK_ICON.encode()))

        # Set the icon as a property of the dialog
        self.setProperty("checkmark", pixmap)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("New Carriers Detected", self)
        layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
            }
            QCheckBox {
                color: #E1E1E1;
                font-size: 12px;
                spacing: 8px;  /* Space between checkbox and text */
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #BB86FC;
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
            }
            QCheckBox::indicator:checked {
                background-color: #BB86FC;
                image: url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb\
3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJ\
NMTAgM0w0LjUgOC41TDIgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91b\
mQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=");
            }
            QCheckBox::indicator:hover {
                border-color: #9965DA;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
        """
        )

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Add label
        label = QLabel("Select the new carriers to add to the carrier list:")
        content_layout.addWidget(label)

        # Add checkboxes for carriers
        self.checkboxes = {}
        for carrier in carriers:
            checkbox = QCheckBox(carrier)
            checkbox.setChecked(False)  # Start unchecked
            self.checkboxes[carrier] = checkbox
            content_layout.addWidget(checkbox)

        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        content_layout.addLayout(button_layout)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Set minimum size and adjust based on content
        self.setMinimumSize(300, 150)
        self.adjustSize()

        # Center on screen if no parent, otherwise center on parent
        if parent:
            parent_center = parent.mapToGlobal(parent.rect().center())
            geometry = self.frameGeometry()
            geometry.moveCenter(parent_center)
            self.move(geometry.topLeft())
        else:
            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            geometry = self.frameGeometry()
            geometry.moveCenter(screen.center())
            self.move(geometry.topLeft())

    def get_selected_carriers(self):
        """Return list of selected carriers.

        Returns:
            list: Names of carriers whose checkboxes are checked
        """
        return [
            carrier
            for carrier, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]

    @staticmethod
    def center_dialog(dialog, parent):
        """Center the dialog on its parent.

        Args:
            dialog (QDialog): The dialog to center
            parent (QWidget): Parent widget to center on
        """
        if parent and parent.isVisible():
            parent_geo = parent.geometry()
            dialog_geo = dialog.geometry()
            x = parent_geo.x() + (parent_geo.width() - dialog_geo.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - dialog_geo.height()) // 2
            dialog.move(x, y)

    @staticmethod
    def get_new_carriers(parent, carriers):
        """Show dialog and return selected carriers.

        Creates and shows the dialog, handling centering and execution.

        Args:
            parent (QWidget): Parent widget
            carriers (list): List of carrier names to display

        Returns:
            list: Names of carriers selected by the user, or empty list if cancelled
        """
        dialog = NewCarriersDialog(carriers, parent)

        # Force the dialog to be centered on the parent window
        if parent:
            # Wait a brief moment to ensure parent window is fully positioned
            QTimer.singleShot(
                100, lambda: NewCarriersDialog.center_dialog(dialog, parent)
            )

        result = dialog.exec_()

        if result == QDialog.Accepted:
            return dialog.get_selected_carriers()
        return []


class CustomSizeGrip(QSizeGrip):
    """Custom size grip widget with classic Windows-style diagonal dots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)

    def paint_event(self, event):
        """Paint the classic diagonal dot pattern."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Define dot color
        dot_color = QColor("#666666")
        hover_color = QColor("#999999")

        # Use hover color if mouse is over the grip
        if self.underMouse():
            dot_color = hover_color

        painter.setPen(Qt.NoPen)
        painter.setBrush(dot_color)

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
