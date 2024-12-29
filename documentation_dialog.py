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
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from custom_widgets import (
    CustomSizeGrip,
    CustomTitleBarWidget,
)
from documentation_content import (
    DOCUMENTATION_85D,
    DOCUMENTATION_85F,
    DOCUMENTATION_85F_5TH,
    DOCUMENTATION_85F_NS,
    DOCUMENTATION_85G,
    DOCUMENTATION_MAX12,
    DOCUMENTATION_MAX60,
)
from theme import (
    ALPHA_HOVER,
    ALPHA_PRESSED,
    COLOR_TEXT_DIM,
    COLOR_TEXT_LIGHT,
    MATERIAL_BACKGROUND,
    MATERIAL_PRIMARY,
    MATERIAL_SURFACE,
    SCROLLBAR_STYLE,
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
        drag_pos: Position for window dragging
    """

    def __init__(self, parent=None):
        """Initialize the documentation dialog.

        Args:
            parent: Parent widget, typically the main application window
        """
        super().__init__(parent)
        self.parent = parent
        self.drag_pos = None
        self.init_ui()

    def init_ui(self):
        """Initialize and configure the dialog's user interface.

        Sets up:
        - Window properties (title, size, flags)
        - Custom title bar
        - Content layout and styling
        - Documentation sections
        """
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setSizeGripEnabled(False)
        self.setMinimumSize(600, 400)
        self.resize(950, 800)

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
        content_layout.setContentsMargins(15, 15, 15, 35)

        # Create and populate tab widget
        tab_widget = QTabWidget()
        self._add_documentation_tabs(tab_widget)
        content_layout.addWidget(tab_widget)

        # Create button container with horizontal layout
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 20, 0)
        button_layout.addStretch()

        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        content_layout.addWidget(button_container)

        layout.addWidget(content_widget)
        self.setLayout(layout)

        # Add custom size grip
        self.size_grip = CustomSizeGrip(self)

        # Center on parent
        if self.parent:
            self.move(
                self.parent.x() + (self.parent.width() - self.width()) // 2,
                self.parent.y() + (self.parent.height() - self.height()) // 2,
            )

    def resizeEvent(self, event):
        """Handle resize events to keep size grip in correct position."""
        super().resizeEvent(event)
        # Update size grip position
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height(),
        )
        self.size_grip.raise_()

    def _setup_styles(self, widget):
        """Set up the stylesheet for the content widget."""
        widget.setStyleSheet(
            f"""
            QWidget {{
                background-color: {MATERIAL_BACKGROUND.name()};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLOR_TEXT_DIM.name()};
                background-color: {MATERIAL_SURFACE.name()};
            }}
            QTabBar::tab {{
                background-color: {MATERIAL_SURFACE.name()};
                color: {COLOR_TEXT_LIGHT.name()};
                padding: 8px 20px;
                margin: 0 2px;
                border: 1px solid {COLOR_TEXT_DIM.name()};
                font-size: 14px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {MATERIAL_PRIMARY.name()};
                color: #000000;
            }}
            QTextBrowser {{
                background-color: {MATERIAL_SURFACE.name()};
                color: {COLOR_TEXT_LIGHT.name()};
                border: none;
                font-size: 14px;
                line-height: 1.6;
            }}
            QPushButton {{
                background-color: {MATERIAL_PRIMARY.name()};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: black;
                min-width: 80px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(187, 134, 252, {ALPHA_HOVER});
            }}
            QPushButton:pressed {{
                background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
            }}
            {SCROLLBAR_STYLE}
            """
        )

    def _add_documentation_tabs(self, tab_widget):
        """Add all documentation tabs to the tab widget."""
        documentation_sections = [
            ("8.5.D", DOCUMENTATION_85D),
            ("8.5.F", DOCUMENTATION_85F),
            ("8.5.F NS", DOCUMENTATION_85F_NS),
            ("8.5.F 5th", DOCUMENTATION_85F_5TH),
            ("8.5.G", DOCUMENTATION_85G),
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
