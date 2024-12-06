from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import CustomTitleBarWidget


class SettingsDialog(QWidget):
    def __init__(self, current_path, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mandates_db_path = current_path

        # Set window flags for frameless window
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar with dragging enabled
        self.title_bar = CustomTitleBarWidget(title="Settings", parent=self)
        layout.addWidget(self.title_bar)

        # Content widget with dark background
        content_widget = QWidget()
        content_widget.setStyleSheet(
            "background-color: #1E1E1E;"
        )  # Dark background to match theme
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(
            20, 20, 20, 20
        )  # Increased margins for better spacing
        content_layout.setSpacing(15)  # Increased spacing between elements

        # Labels with better styling
        path_label = QLabel("Current Database Path")
        path_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")

        self.path_display = QLabel(self.mandates_db_path)
        self.path_display.setStyleSheet(
            """
            color: #9575CD;  /* Lighter purple for path */
            font-size: 11px;
            padding: 5px;
        """
        )
        self.path_display.setWordWrap(True)

        status_label = QLabel("Status")
        status_label.setStyleSheet(
            "color: #FFFFFF; font-size: 12px; font-weight: bold;"
        )

        self.status_display = QLabel("Connected ✓")
        self.status_display.setStyleSheet(
            """
            color: #81C784;  /* Material green */
            font-size: 11px;
            padding: 5px;
        """
        )

        # Buttons with material styling
        button_style = """
            QPushButton {
                background-color: #9575CD;  /* Material purple */
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #B39DDB;  /* Lighter purple on hover */
            }
            QPushButton:pressed {
                background-color: #7E57C2;  /* Darker purple when pressed */
            }
        """

        set_path_button = QPushButton("Set Database Path")
        set_path_button.clicked.connect(self.set_database_path)
        set_path_button.setFixedWidth(200)
        set_path_button.setStyleSheet(button_style)

        save_button = QPushButton("Save and Close")
        save_button.clicked.connect(self.accept)
        save_button.setFixedWidth(200)
        save_button.setStyleSheet(button_style)

        # Add widgets to content layout
        content_layout.addWidget(path_label)
        content_layout.addWidget(self.path_display)
        content_layout.addSpacing(10)  # Additional spacing between sections
        content_layout.addWidget(status_label)
        content_layout.addWidget(self.status_display)
        content_layout.addSpacing(20)  # More spacing before buttons
        content_layout.addWidget(set_path_button, alignment=Qt.AlignCenter)
        content_layout.addWidget(save_button, alignment=Qt.AlignCenter)
        content_layout.addStretch()  # Push everything up

        # Add content widget to main layout
        layout.addWidget(content_widget)

        # Set a fixed size
        self.setFixedSize(400, 337)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragPos is not None:
            self.move(event.globalPos() - self.dragPos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = None
            event.accept()

    def accept(self):
        self.hide()

    def set_database_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            "",
            "SQLite Database (*.sqlite);;All Files (*.*)",
        )
        if file_path:
            self.mandates_db_path = file_path
            self.path_display.setText(self.mandates_db_path)
