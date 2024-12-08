"""Application documentation and help dialog.

This module provides a dialog interface for displaying application documentation,
including:
- Feature guides and tutorials
- Usage instructions
- Keyboard shortcuts
- Troubleshooting tips
- Version information

The dialog uses a custom title bar and supports markdown-formatted content
with proper styling and navigation.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import CustomTitleBarWidget
from documentation_content import (
    DOCUMENTATION_85D,
    DOCUMENTATION_85F,
    DOCUMENTATION_85F_5TH,
    DOCUMENTATION_85F_NS,
    DOCUMENTATION_MAX12,
    DOCUMENTATION_MAX60,
)


class DocumentationDialog(QDialog):
    """Dialog for displaying application documentation and help content.

    Provides a styled interface for viewing documentation with:
    - Custom title bar with window controls
    - Markdown content rendering
    - Organized sections and navigation
    - Responsive layout
    - Window dragging support

    Attributes:
        parent: Parent widget (usually main window)
        dragPos: Position for window dragging
    """

    def __init__(self, parent=None):
        """Initialize the documentation dialog.

        Args:
            parent: Parent widget, typically the main application window
        """
        super().__init__(parent)
        self.parent = parent
        self.dragPos = None
        self.initUI()

    def initUI(self):
        """Initialize and configure the dialog's user interface.

        Sets up:
        - Window properties (title, size, flags)
        - Custom title bar
        - Content layout and styling
        - Documentation sections
        """
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setSizeGripEnabled(True)
        self.setMinimumSize(800, 600)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("Article 8 Violation Formulas", self)
        layout.addWidget(self.title_bar)

        # Create content widget and add styling
        content_widget = QWidget()
        self._setup_styles(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)

        # Create and populate tab widget
        tab_widget = QTabWidget()
        self._add_documentation_tabs(tab_widget)
        content_layout.addWidget(tab_widget)

        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        content_layout.addWidget(close_button, alignment=Qt.AlignRight)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Center on parent
        if self.parent:
            self.move(
                self.parent.x() + (self.parent.width() - self.width()) // 2,
                self.parent.y() + (self.parent.height() - self.height()) // 2,
            )

    def _setup_styles(self, widget):
        """Set up the stylesheet for the content widget."""
        widget.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #E1E1E1;
                padding: 8px 20px;
                margin: 0 2px;
                border: 1px solid #333333;
                font-size: 14px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #BB86FC;
                color: #000000;
            }
            QTextBrowser {
                background-color: #1E1E1E;
                color: #E1E1E1;
                border: none;
                font-size: 14px;
                line-height: 1.6;
            }
            QPushButton {
                background-color: #BB86FC;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #9965DA;
            }
            QPushButton:pressed {
                background-color: #7B4FAF;
            }
            """
        )

    def _add_documentation_tabs(self, tab_widget):
        """Add all documentation tabs to the tab widget."""
        documentation_sections = [
            ("8.5.D", DOCUMENTATION_85D),
            ("8.5.F", DOCUMENTATION_85F),
            ("8.5.F NS", DOCUMENTATION_85F_NS),
            ("8.5.F 5th", DOCUMENTATION_85F_5TH),
            ("MAX12", DOCUMENTATION_MAX12),
            ("MAX60", DOCUMENTATION_MAX60),
        ]

        for title, content in documentation_sections:
            self.add_violation_tab(tab_widget, title, content)

    def add_violation_tab(self, tab_widget, title, content):
        """Add a single documentation tab to the tab widget."""
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(content)
        tab_widget.addTab(text_browser, title)

    def accept(self):
        """Close the dialog.

        Overrides QDialog's accept method to handle custom close behavior.
        """
        self.hide()
