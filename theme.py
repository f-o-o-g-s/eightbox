# theme.py
"""Application theming and style management.

This module defines the application's visual theme and styling, including:
- Material Design dark theme implementation
- Color schemes for UI elements (background, text, borders)
- Accent colors for different states (active, hover, pressed)
- Semantic colors (success, warning, error)
- Font styles and sizes
- Widget styling (QSS)
- Layout spacing and margins
- Custom widget appearance

The theme follows Material Design principles with a dark mode focus,
ensuring consistent styling across all application components.

Color Constants:
    MATERIAL_PRIMARY: Primary brand color (purple)
    MATERIAL_PRIMARY_VARIANT: Darker primary for contrast
    MATERIAL_SECONDARY: Accent color (teal)
    MATERIAL_BACKGROUND: Main background color
    MATERIAL_SURFACE: Elevated surface color
    MATERIAL_ERROR: Error state color
    COLOR_ROW_HIGHLIGHT: Table row hover color
    COLOR_CELL_HIGHLIGHT: Selected cell color
    COLOR_WEEKLY_REMEDY: Weekly totals highlight
    COLOR_TEXT_LIGHT: Primary text color
    COLOR_TEXT_DIM: Secondary text color
    COLOR_MAXIMIZED_TRUE: Success state color
    COLOR_MAXIMIZED_FALSE: Error state color
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QStyleFactory,
)

# Material Design Dark Theme Colors
MATERIAL_PRIMARY = QColor("#BB86FC")  # Primary brand color (purple)
MATERIAL_PRIMARY_VARIANT = QColor("#3700B3")  # Darker primary for contrast
MATERIAL_SECONDARY = QColor("#03DAC6")  # Accent color (teal)
MATERIAL_BACKGROUND = QColor("#121212")  # Main background
MATERIAL_SURFACE = QColor("#1E1E1E")  # Elevated surface color
MATERIAL_ERROR = QColor("#CF6679")  # Error states

# Application-specific color mappings
COLOR_ROW_HIGHLIGHT = QColor("#2D2D2D")  # Table row hover
COLOR_CELL_HIGHLIGHT = MATERIAL_PRIMARY.darker(150)  # Selected cell
COLOR_WEEKLY_REMEDY = MATERIAL_SECONDARY.darker(150)  # Weekly totals
COLOR_NO_HIGHLIGHT = MATERIAL_SURFACE  # Default state
COLOR_TEXT_LIGHT = QColor("#E1E1E1")  # Primary text
COLOR_TEXT_DIM = QColor("#333333")  # Secondary text
COLOR_MAXIMIZED_TRUE = QColor("#4CAF50")  # Success state
COLOR_MAXIMIZED_FALSE = QColor("#F44336")  # Error state

# Violation-specific colors (matching violation_model.py)
COLOR_VIOLATION = QColor("#7D59A8")  # Medium dark purple (125, 89, 168)
COLOR_VIOLATION_SUMMARY = QColor("#D7B7FF")  # Light purple (215, 183, 255)
COLOR_VIOLATION_WEEKLY = QColor("#029184")  # Teal (2, 145, 132)

# Component-specific style sheets
TITLE_BAR_STYLE = """
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

CLOSE_BUTTON_STYLE = "QPushButton:hover { background-color: #c42b1c; }"

TOP_BUTTON_ROW_STYLE = """
    QWidget {
        background-color: #121212;  /* Material Dark background */
        border-bottom: 1px solid #2D2D2D;
    }
    QPushButton {
        background-color: rgba(187, 134, 252, 0.05);  /* Primary color with 5% opacity */
        border: none;
        border-radius: 4px;
        color: #BB86FC;  /* Primary color */
        padding: 16px 32px;  /* Increased padding */
        font-size: 14px;  /* Increased font size */
        font-weight: 500;
        text-align: center;
        margin: 12px 6px;  /* Increased margins */
        min-width: 180px;  /* Increased width */
        letter-spacing: 0.15px;
        text-transform: uppercase;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.08);
        color: #CBB0FF;
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.12);
        padding-top: 17px;
        color: #BB86FC;
    }
    QPushButton:checked {
        background-color: rgba(187, 134, 252, 0.12);
        color: #E9B7FF;
        font-weight: 600;
    }
    QPushButton:checked:hover {
        background-color: rgba(187, 134, 252, 0.16);
    }
    QPushButton:disabled {
        background-color: rgba(255, 255, 255, 0.12);
        color: rgba(255, 255, 255, 0.38);
    }
"""

FILTER_BUTTON_ROW_STYLE = """
    QWidget {
        background-color: #121212;
        border-top: 1px solid #333333;
    }
    QPushButton {
        background-color: rgba(187, 134, 252, 0.05);
        border: none;
        color: rgba(187, 134, 252, 0.87);
        padding: 4px 12px;
        font-size: 12px;
        margin: 1px;
        min-width: 90px;
        max-height: 24px;
        border-radius: 4px;
        text-align: center;
        font-weight: 500;
        letter-spacing: 0.15px;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.08);
        color: rgba(187, 134, 252, 1.0);
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.12);
        color: rgba(187, 134, 252, 1.0);
    }
    QPushButton:checked {
        background-color: rgba(187, 134, 252, 0.12);
        color: rgba(187, 134, 252, 1.0);
        font-weight: 600;
    }
    QLabel {
        color: rgba(187, 134, 252, 0.87);
        font-size: 12px;
        padding: 4px 12px;
        background-color: rgba(187, 134, 252, 0.05);
        border-radius: 4px;
        font-weight: 500;
        letter-spacing: 0.15px;
    }
"""

TAB_WIDGET_STYLE = """
    QTabWidget::pane {
        border: none;
        background-color: #121212;
    }
    QTabBar {
        qproperty-drawBase: 0;
    }
    QTabBar::tab {
        background-color: #1E1E1E;
        color: rgba(255, 255, 255, 0.6);
        padding: 8px 16px;
        border: none;
        border-right: 1px solid #2D2D2D;
        min-width: 80px;
        font: 11px;
    }
    QTabBar::tab:selected {
        color: #BB86FC;
        background-color: rgba(187, 134, 252, 0.12);
        border-bottom: 2px solid #BB86FC;
    }
    QTabBar::tab:hover {
        background-color: rgba(187, 134, 252, 0.08);
        color: #CBB0FF;
    }
    QTabBar::scroller {
        width: 0px;
    }
"""

SUB_TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background-color: #121212;
        padding-top: 2px;
    }
    QTabBar {
        qproperty-drawBase: 0;
    }
    QTabBar::tab {
        background-color: #1A1A1A;
        color: rgba(255, 255, 255, 0.6);
        padding: 6px 12px;
        min-width: 60px;
        margin: 0;
        border-right: 1px solid #2D2D2D;
        font-size: 10px;
        font-weight: normal;
        text-transform: uppercase;
        letter-spacing: 0.05px;
    }
    QTabBar::tab:hover {
        background-color: rgba(187, 134, 252, 0.08);
        color: #CBB0FF;
    }
    QTabBar::tab:selected {
        color: #BB86FC;
        border-bottom: 2px solid #BB86FC;
        background-color: rgba(187, 134, 252, 0.12);
        border-right: 1px solid #BB86FC;
        font-weight: 500;
    }
    QTabBar::scroller {
        width: 0px;
    }
"""

MENU_BAR_STYLE = """
    QMenuBar {
        background-color: #455A64;
        color: white;
        border: none;
        padding: 2px;
    }
    QMenuBar::item {
        background-color: transparent;
        padding: 4px 10px;
    }
    QMenuBar::item:selected {
        background-color: #546E7A;
    }
    QMenuBar::item:pressed {
        background-color: #37474F;
    }
    QMenu {
        background-color: #455A64;
        color: white;
        border: 1px solid #546E7A;
    }
    QMenu::item:selected {
        background-color: #546E7A;
    }
"""

FILTER_ROW_STYLE = """
    QWidget {
        background-color: #1E1E1E;
        border-bottom: 1px solid #333333;
    }
    QLineEdit {
        background-color: #2D2D2D;
        color: #E1E1E1;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 8px;
        margin: 8px;
    }
    QLineEdit:focus {
        border: 1px solid #BB86FC;
    }
    QLineEdit::placeholder {
        color: #808080;
    }
"""

SIZE_GRIP_STYLE = "background: transparent;"

# Settings Dialog Styles
SECTION_FRAME_STYLE = """
    QFrame#sectionFrame {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-radius: 8px;
    }
"""

SETTINGS_DIALOG_STYLE = """
    QDialog {
        background-color: #121212;
    }
    QPushButton {
        background-color: rgba(187, 134, 252, 0.1);
        border: none;
        border-radius: 4px;
        color: #BB86FC;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        min-width: 120px;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.15);
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.2);
    }
    QLabel {
        color: #E1E1E1;
    }
"""

SETTINGS_PATH_DISPLAY_STYLE = """
    color: #9575CD;
    font-size: 11px;
    padding: 8px;
    background-color: rgba(30, 30, 30, 0.6);
    border-radius: 4px;
    border: 1px solid #333333;
"""

SETTINGS_STATUS_STYLE = """
    color: #81C784;
    font-size: 11px;
    padding: 8px;
    font-weight: 500;
"""

SETTINGS_STATUS_ERROR_STYLE = """
    color: #EF5350;
    font-size: 11px;
    padding: 5px;
"""

SETTINGS_BUTTON_CONTAINER_STYLE = """
    QWidget#buttonContainer {
        background-color: #1A1A1A;
        border-radius: 8px;
        border: 1px solid #333333;
    }
"""

SETTINGS_SYNC_BUTTON_STYLE = """
    QPushButton {
        background-color: rgba(187, 134, 252, 0.1);
        border: none;
        border-radius: 4px;
        color: #BB86FC;
        padding: 12px 24px;
        font-size: 13px;
        font-weight: 500;
        min-width: 200px;
        text-align: center;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.15);
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.2);
        padding-top: 13px;
        padding-bottom: 11px;
    }
"""

SETTINGS_CLOSE_BUTTON_STYLE = """
    QPushButton {
        background-color: rgba(255, 255, 255, 0.05);
        border: none;
        border-radius: 4px;
        color: #E1E1E1;
        padding: 12px 24px;
        font-size: 13px;
        font-weight: 500;
        min-width: 200px;
        text-align: center;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 0.08);
    }
    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 0.12);
        padding-top: 13px;
        padding-bottom: 11px;
    }
"""

DATE_SELECTION_PANE_STYLE = """
    QWidget {
        background-color: #121212;
    }
    QLabel {
        color: #E1E1E1;
        font-size: 13px;
        padding: 8px;
        background-color: #1E1E1E;
        border-radius: 4px;
    }
    QTableView {
        background-color: #121212;
        border: none;
        border-radius: 4px;
        selection-background-color: #BB86FC;
        selection-color: #000000;
        gridline-color: transparent;
    }
    QTableView::item {
        padding: 8px;
        border-radius: 2px;
    }
    QTableView::item:hover {
        background-color: rgba(187, 134, 252, 0.1);
    }
    QTableView::item:selected {
        background-color: #BB86FC;
        color: #000000;
    }
    QHeaderView::section {
        background-color: #1E1E1E;
        color: #BB86FC;
        font-weight: bold;
        padding: 8px;
        border: none;
        border-radius: 0px;
    }
    QHeaderView::section:first {
        border-top-left-radius: 4px;
        border-bottom-left-radius: 4px;
    }
    QHeaderView::section:last {
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }
    QPushButton {
        background-color: #2D2D2D;
        color: #BB86FC;
        border: 1px solid #3D3D3D;
        border-bottom: 2px solid #1D1D1D;
        padding: 8px 24px;
        font-weight: 500;
        min-height: 32px;
        border-radius: 4px;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QPushButton:hover {
        background-color: #353535;
        border: 1px solid #454545;
        border-bottom: 2px solid #252525;
        color: #CBB0FF;
    }
    QPushButton:pressed {
        background-color: #252525;
        border: 1px solid #353535;
        border-top: 2px solid #151515;
        border-bottom: 1px solid #353535;
        padding-top: 9px;
        color: #BB86FC;
    }
    QPushButton:disabled {
        background-color: #252525;
        color: rgba(225, 225, 225, 0.3);
        border: 1px solid #2D2D2D;
    }
    QScrollBar:vertical {
        background-color: #121212;
        width: 12px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #424242;
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #616161;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
"""

# Custom Widget Styles
CUSTOM_TITLE_BAR_STYLE = """
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

CUSTOM_PROGRESS_DIALOG_STYLE = """
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
    QPushButton {
        background-color: rgba(255, 255, 255, 0.05);
        color: #E1E1E1;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 8px 24px;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 120px;
        margin: 8px 0px;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.15);
        border: 1px solid #BB86FC;
        color: #BB86FC;
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.25);
        padding-top: 9px;
        padding-bottom: 7px;
    }
    QPushButton:disabled {
        background-color: rgba(255, 255, 255, 0.03);
        color: rgba(255, 255, 255, 0.38);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
"""

CUSTOM_MESSAGE_BOX_STYLE = """
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

CUSTOM_WARNING_DIALOG_STYLE = """
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

CUSTOM_INFO_DIALOG_STYLE = """
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

CUSTOM_NOTIFICATION_DIALOG_STYLE = """
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

CONFIRM_DIALOG_STYLE = """
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

NEW_CARRIERS_DIALOG_STYLE = """
    QWidget {
        background-color: #1E1E1E;
        color: #E1E1E1;
    }
    QLabel {
        color: #E1E1E1;
        font-size: 12px;
        padding: 4px;
    }
    QCheckBox {
        color: #E1E1E1;
        font-size: 12px;
        padding: 4px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #BB86FC;
        border-radius: 4px;
        background-color: transparent;
    }
    QCheckBox::indicator:checked {
        background-color: #BB86FC;
        image: url(resources/check.png);
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
    QPushButton#secondary {
        background-color: #2D2D2D;
        color: #BB86FC;
        border: 1px solid #BB86FC;
    }
    QPushButton#secondary:hover {
        background-color: #353535;
    }
    QPushButton#secondary:pressed {
        background-color: #252525;
    }
"""

# Clean Moves Dialog Styles
CLEAN_MOVES_DIALOG_STYLE = """
    QDialog {
        background-color: #121212;
        color: #E1E1E1;
    }
    QTableWidget {
        background-color: #1E1E1E;
        alternate-background-color: #262626;
        color: #E1E1E1;
        border: 1px solid #333333;
        gridline-color: #333333;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QTableWidget::item:selected {
        background-color: #3700B3;
        color: #FFFFFF;
    }
    QHeaderView::section {
        background-color: #2D2D2D;
        color: #E1E1E1;
        padding: 5px;
        border: 1px solid #333333;
    }
    QPushButton {
        background-color: rgba(187, 134, 252, 0.1);
        color: #BB86FC;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.2);
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.3);
    }
    QPushButton:disabled {
        background-color: #1E1E1E;
        color: #666666;
    }
    QLabel {
        color: #E1E1E1;
    }
"""

SPLIT_MOVE_DIALOG_STYLE = """
    QDialog {
        background-color: #121212;
        color: #E1E1E1;
    }
    QGroupBox {
        background-color: #1E1E1E;
        color: #E1E1E1;
        border: 1px solid #333333;
        border-radius: 4px;
        padding: 15px;
        margin-top: 15px;
    }
    QGroupBox::title {
        color: #BB86FC;
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    QLineEdit {
        background-color: #2D2D2D;
        color: #E1E1E1;
        border: 1px solid #333333;
        padding: 5px;
        border-radius: 4px;
    }
    QLineEdit:focus {
        border: 1px solid #BB86FC;
    }
    QLineEdit:disabled {
        background-color: #1E1E1E;
        color: #666666;
        border: 1px solid #333333;
    }
    QPushButton {
        background-color: rgba(187, 134, 252, 0.1);
        color: #BB86FC;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: rgba(187, 134, 252, 0.2);
    }
    QPushButton:pressed {
        background-color: rgba(187, 134, 252, 0.3);
    }
    QPushButton:disabled {
        background-color: #1E1E1E;
        color: #666666;
    }
    QLabel {
        color: #E1E1E1;
    }
"""

CLEAN_MOVES_SAVE_BUTTON_STYLE = """
    QPushButton {
        background-color: #2D2D2D;
        color: #BB86FC;
        border: 1px solid #3D3D3D;
        border-bottom: 2px solid #1D1D1D;
        padding: 8px 24px;
        font-weight: 500;
        min-height: 32px;
        border-radius: 4px;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QPushButton:hover {
        background-color: #353535;
        border: 1px solid #454545;
        border-bottom: 2px solid #252525;
        color: #CBB0FF;
    }
    QPushButton:pressed {
        background-color: #252525;
        border: 1px solid #353535;
        border-top: 2px solid #151515;
        border-bottom: 1px solid #353535;
        padding-top: 9px;
        color: #BB86FC;
    }
    QPushButton:disabled {
        background-color: #252525;
        color: #666666;
        border: 1px solid #2D2D2D;
    }
"""

CLEAN_MOVES_CANCEL_BUTTON_STYLE = CLEAN_MOVES_SAVE_BUTTON_STYLE

DISABLED_START_INPUT_STYLE = """
    QLineEdit:disabled {
        background-color: #1E1E1E;
        color: #808080;
        border: 1px solid #404040;
    }
"""


def apply_material_dark_theme(app: QApplication):
    """Apply Material Dark theme to the entire application.

    Configures the application-wide dark theme using Material Design principles.
    This includes setting up:
    - Color palette for all UI elements
    - Custom styling for widgets
    - Typography and spacing
    - Interactive states (hover, pressed, etc.)

    Args:
        app (QApplication): The main application instance to theme
    """
    app.setStyle(QStyleFactory.create("Fusion"))

    # Create dark palette
    dark_palette = app.palette()
    dark_palette.setColor(dark_palette.Window, MATERIAL_BACKGROUND)
    dark_palette.setColor(dark_palette.WindowText, COLOR_TEXT_LIGHT)
    dark_palette.setColor(dark_palette.Base, MATERIAL_SURFACE)
    dark_palette.setColor(dark_palette.AlternateBase, MATERIAL_BACKGROUND)
    dark_palette.setColor(dark_palette.ToolTipBase, COLOR_TEXT_LIGHT)
    dark_palette.setColor(dark_palette.ToolTipText, COLOR_TEXT_LIGHT)
    dark_palette.setColor(dark_palette.Text, COLOR_TEXT_LIGHT)
    dark_palette.setColor(dark_palette.Button, MATERIAL_SURFACE)
    dark_palette.setColor(dark_palette.ButtonText, COLOR_TEXT_LIGHT)
    dark_palette.setColor(dark_palette.Link, MATERIAL_PRIMARY)
    dark_palette.setColor(dark_palette.Highlight, MATERIAL_PRIMARY)
    dark_palette.setColor(dark_palette.HighlightedText, COLOR_TEXT_LIGHT)

    app.setPalette(dark_palette)

    # Global stylesheet for material look
    app.setStyleSheet(
        """
        QMainWindow, QDialog {
            background-color: #121212;
        }
        QWidget {
            font-family: Roboto, Arial, sans-serif;
        }
        QPushButton {
            background-color: rgba(187, 134, 252, 0.1);
            border: none;
            color: #BB86FC;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: normal;
        }
        QPushButton:hover {
            background-color: rgba(187, 134, 252, 0.2);
        }
        QPushButton:pressed {
            background-color: rgba(187, 134, 252, 0.3);
        }
        QPushButton:checked {
            background-color: #BB86FC;
            color: #000000;
        }
        QTableView {
            background-color: #1E1E1E;
            alternate-background-color: #262626;
            selection-background-color: #3700B3;
            selection-color: #FFFFFF;
            gridline-color: #333333;
            border-radius: 4px;
        }
        QTableView::item {
            /* Keep minimal styling to not interfere with dynamic colors */
        }
        QHeaderView::section {
            background-color: #2D2D2D;
            color: #E1E1E1;
            padding: 4px;
            border: 1px solid #333333;
        }
        QHeaderView::section:first {
            border-top-left-radius: 4px;
        }
        QHeaderView::section:last {
            border-top-right-radius: 4px;
        }
        QTableCornerButton::section {
            background-color: #1E1E1E;
            border: none;
        }
        QTableView::item:focus {
            border: none;
            outline: none;
        }
        QTabWidget::pane {
            border: 1px solid #333333;
        }
        QTabBar::tab {
            background-color: #1E1E1E;
            color: #9E9E9E;
            padding: 8px 16px;
            border: 1px solid #333333;
        }
        QTabBar::tab:selected {
            background-color: #BB86FC;
            color: #000000;
        }
        QLineEdit {
            background-color: #2D2D2D;
            color: #E1E1E1;
            border: 1px solid #333333;
            padding: 4px;
            border-radius: 4px;
        }
        QComboBox {
            background-color: #2D2D2D;
            color: #E1E1E1;
            border: 1px solid #333333;
            padding: 4px;
            border-radius: 4px;
        }
        QScrollBar {
            background-color: #1E1E1E;
            border: none;
        }
        QScrollBar:vertical {
            width: 10px;
        }
        QScrollBar:horizontal {
            height: 10px;
        }
        QScrollBar::handle {
            background-color: #424242;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:hover {
            background-color: #616161;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            width: 0px;
            height: 0px;
            background: none;
            border: none;
        }
        QScrollBar::add-page, QScrollBar::sub-page {
            background: none;
        }
        /* Dialog Styling */
        QDialog {
            background-color: #121212;
            border: none;
            padding: 1px;
        }
        QDialog > QWidget {
            background-color: #121212;
            border: 2px solid #1A1A1A;
            border-bottom: 2px solid #252525;
        }
        QDialog QLabel {
            color: #FFFFFF;
        }
        QDialog QPushButton {
            min-width: 250px;
        }
        /* Top Button Row Styling */
        QWidget#ButtonContainer {
            background-color: #1E1E1E;
            border-bottom: 1px solid #333333;
        }
        QWidget#ButtonContainer QPushButton {
            background-color: transparent;
            border: none;
            color: #E1E1E1;
            padding: 12px 24px;
            font-size: 13px;
            font-weight: normal;
            text-align: left;
        }
        QWidget#ButtonContainer QPushButton:hover {
            background-color: #2D2D2D;
        }
        QWidget#ButtonContainer QPushButton:pressed,
        QWidget#ButtonContainer QPushButton:checked {
            background-color: #BB86FC;
            color: #000000;
        }
    """
    )
