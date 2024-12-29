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

# Alpha values for states
ALPHA_HOVER = 0.1
ALPHA_PRESSED = 0.15
ALPHA_SELECTED = 0.2
ALPHA_DISABLED = 0.05
ALPHA_DISABLED_TEXT = 0.3  # For disabled text elements

# Material Design Dark Theme Colors
MATERIAL_PRIMARY = QColor("#BB86FC")  # Primary brand color (purple)
MATERIAL_PRIMARY_VARIANT = QColor("#3700B3")  # Darker primary for contrast
MATERIAL_SECONDARY = QColor("#03DAC6")  # Accent color (teal)
MATERIAL_BACKGROUND = QColor("#121212")  # Main background
MATERIAL_SURFACE = QColor("#1E1E1E")  # Elevated surface color
MATERIAL_ERROR = QColor("#CF6679")  # Error states

# Additional Material Design Colors
MATERIAL_BLUE_GREY_800 = QColor("#37474F")  # Header backgrounds
MATERIAL_BLUE_GREY_900 = QColor("#263238")  # Day name backgrounds
MATERIAL_RED_900 = QColor("#B71C1C")  # Error states
MATERIAL_RED_200 = QColor("#EF9A9A")  # Error text
MATERIAL_GREEN_900 = QColor("#1B5E20")  # Success states
MATERIAL_GREEN_300 = QColor("#81C784")  # Success text
MATERIAL_GREY_600 = QColor("#666666")  # Dot color
MATERIAL_GREY_700 = QColor("#999999")  # Hover color
MATERIAL_GREY_800 = QColor("#424242")  # Checkbox unchecked
MATERIAL_BLUE_600 = QColor("#1976D2")  # Checkbox checked
MATERIAL_BLUE_GREY_700 = QColor("#455A64")  # Title bar hover
MATERIAL_RED_700 = QColor("#c42b1c")  # Close button hover

# Basic Colors
COLOR_BLACK = QColor("#000000")  # Pure black for text
COLOR_WHITE = QColor("#FFFFFF")  # Pure white for text

# Application-specific color mappings
COLOR_ROW_HIGHLIGHT = QColor("#2D2D2D")  # Table row hover
COLOR_CELL_HIGHLIGHT = MATERIAL_PRIMARY.darker(150)  # Selected cell
COLOR_WEEKLY_REMEDY = MATERIAL_SECONDARY.darker(150)  # Weekly totals
COLOR_NO_HIGHLIGHT = MATERIAL_SURFACE  # Default state
COLOR_TEXT_LIGHT = QColor("#E1E1E1")  # Primary text
COLOR_TEXT_DIM = QColor("#333333")  # Secondary text
COLOR_MAXIMIZED_TRUE = QColor("#4CAF50")  # Success state
COLOR_MAXIMIZED_FALSE = QColor("#F44336")  # Error state

# Violation-specific colors
COLOR_VIOLATION = QColor("#7D59A8")  # Medium dark purple (125, 89, 168)
COLOR_VIOLATION_SUMMARY = QColor("#D7B7FF")  # Light purple (215, 183, 255)
COLOR_VIOLATION_WEEKLY = QColor("#029184")  # Teal (2, 145, 132)

# Status-specific colors
COLOR_STATUS_OTDL = MATERIAL_PRIMARY  # Purple for OTDL
COLOR_STATUS_WAL = MATERIAL_SECONDARY  # Teal for WAL
COLOR_STATUS_NL = QColor("#64DD17")  # Light Green for NL
COLOR_STATUS_PTF = QColor("#FF7597")  # Pink for PTF

# Background colors
COLOR_BG_DARKER = QColor("#222222")  # Darker background
COLOR_BG_DARK = QColor("#2A2A2A")  # Dark background
COLOR_BG_HOVER = QColor("#252525")  # Hover background

# Component-specific style sheets
TITLE_BAR_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BLUE_GREY_800.name()};
        border: none;
    }}
    QLabel {{
        color: {COLOR_WHITE.name()};
        font-size: 12pt;
        font-weight: bold;
        background-color: transparent;
    }}
    QPushButton {{
        background-color: transparent;
        border: none;
        color: {COLOR_WHITE.name()};
        padding: 5px;
        min-width: 40px;
        max-width: 40px;
        font-size: 16pt;
        font-family: Arial;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_BLUE_GREY_700.name()};
    }}
"""

CLOSE_BUTTON_STYLE = (
    f"QPushButton:hover {{ background-color: {MATERIAL_RED_700.name()}; }}"
)

TOP_BUTTON_ROW_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BACKGROUND.name()};
        border-bottom: 1px solid {COLOR_ROW_HIGHLIGHT.name()};
    }}
    QPushButton {{
        background-color: rgba(187, 134, 252, {ALPHA_DISABLED});
        border: none;
        border-radius: 4px;
        color: {MATERIAL_PRIMARY.name()};
        padding: 16px 32px;
        font-size: 14px;
        font-weight: 500;
        text-align: center;
        margin: 12px 6px;
        min-width: 180px;
        letter-spacing: 0.15px;
        text-transform: uppercase;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        color: {MATERIAL_PRIMARY.lighter(110).name()};
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        padding-top: 17px;
        color: {MATERIAL_PRIMARY.name()};
    }}
    QPushButton:checked {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        color: {MATERIAL_PRIMARY.lighter(110).name()};
        font-weight: 600;
    }}
    QPushButton:checked:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
    }}
    QPushButton:disabled {{
        background-color: rgba(255, 255, 255, {ALPHA_DISABLED});
        color: rgba(255, 255, 255, {ALPHA_DISABLED_TEXT});
    }}
"""

FILTER_BUTTON_ROW_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BACKGROUND.name()};
        border-top: 1px solid {COLOR_TEXT_DIM.name()};
    }}
    QPushButton {{
        background-color: rgba(187, 134, 252, {ALPHA_DISABLED});
        border: none;
        color: {MATERIAL_PRIMARY.name()};
        padding: 4px 12px;
        font-size: 12px;
        margin: 1px;
        min-width: 90px;
        max-height: 24px;
        border-radius: 4px;
        text-align: center;
        font-weight: 500;
        letter-spacing: 0.15px;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        color: {MATERIAL_PRIMARY.name()};
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        color: {MATERIAL_PRIMARY.name()};
    }}
    QPushButton:checked {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        color: {MATERIAL_PRIMARY.name()};
        font-weight: 600;
    }}
    QLabel {{
        color: {MATERIAL_PRIMARY.name()};
        font-size: 12px;
        padding: 4px 12px;
        font-weight: 500;
        letter-spacing: 0.15px;
    }}
"""

TAB_WIDGET_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background-color: {MATERIAL_BACKGROUND.name()};
    }}
    QTabBar {{
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background-color: {MATERIAL_SURFACE.name()};
        color: rgba(255, 255, 255, {ALPHA_DISABLED_TEXT});
        padding: 8px 16px;
        border: none;
        border-right: 1px solid {COLOR_ROW_HIGHLIGHT.name()};
        min-width: 80px;
        font: 11px;
    }}
    QTabBar::tab:selected {{
        color: {MATERIAL_PRIMARY.name()};
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        border-bottom: 2px solid {MATERIAL_PRIMARY.name()};
    }}
    QTabBar::tab:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        color: {MATERIAL_PRIMARY.lighter(110).name()};
    }}
    QTabBar::scroller {{
        width: 0px;
    }}
"""

SUB_TAB_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background-color: {MATERIAL_BACKGROUND.name()};
        padding-top: 2px;
    }}
    QTabBar {{
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background-color: {MATERIAL_SURFACE.name()};
        color: rgba(255, 255, 255, {ALPHA_DISABLED_TEXT});
        padding: 6px 12px;
        min-width: 60px;
        margin: 0;
        border-right: 1px solid {COLOR_ROW_HIGHLIGHT.name()};
        font-size: 10px;
        font-weight: normal;
        text-transform: uppercase;
        letter-spacing: 0.05px;
    }}
    QTabBar::tab:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        color: {MATERIAL_PRIMARY.lighter(110).name()};
    }}
    QTabBar::tab:selected {{
        color: {MATERIAL_PRIMARY.name()};
        border-bottom: 2px solid {MATERIAL_PRIMARY.name()};
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        border-right: 1px solid {MATERIAL_PRIMARY.name()};
    }}
    QTabBar::scroller {{
        width: 0px;
    }}
"""

MENU_BAR_STYLE = f"""
    QMenuBar {{
        background-color: {MATERIAL_BLUE_GREY_800.name()};
        color: {COLOR_WHITE.name()};
        border: none;
        padding: 2px;
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 10px;
    }}
    QMenuBar::item:selected {{
        background-color: {MATERIAL_BLUE_GREY_700.name()};
    }}
    QMenuBar::item:pressed {{
        background-color: {MATERIAL_BLUE_GREY_900.name()};
    }}
    QMenu {{
        background-color: {MATERIAL_BLUE_GREY_800.name()};
        color: {COLOR_WHITE.name()};
        border: 1px solid {MATERIAL_BLUE_GREY_700.name()};
    }}
    QMenu::item:selected {{
        background-color: {MATERIAL_BLUE_GREY_700.name()};
    }}
"""

FILTER_ROW_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        border-bottom: 1px solid {COLOR_TEXT_DIM.name()};
    }}
    QLineEdit {{
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        border-radius: 4px;
        padding: 8px;
        margin: 8px;
    }}
    QLineEdit:focus {{
        border: 1px solid {MATERIAL_PRIMARY.name()};
    }}
    QLineEdit::placeholder {{
        color: {COLOR_TEXT_DIM.lighter(150).name()};
    }}
"""

SIZE_GRIP_STYLE = "background: transparent;"

# Settings Dialog Styles
SECTION_FRAME_STYLE = f"""
    QFrame#sectionFrame {{
        background-color: {MATERIAL_SURFACE.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
        border-radius: 8px;
    }}
"""

SETTINGS_DIALOG_STYLE = f"""
    QDialog {{
        background-color: {MATERIAL_BACKGROUND.name()};
    }}
    QPushButton {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        border: none;
        border-radius: 4px;
        color: {MATERIAL_PRIMARY.name()};
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        min-width: 120px;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
    }}
"""

SETTINGS_PATH_DISPLAY_STYLE = f"""
    color: {MATERIAL_PRIMARY.lighter(120).name()};
    font-size: 11px;
    padding: 8px;
    background-color: rgba(30, 30, 30, {ALPHA_DISABLED_TEXT});
    border-radius: 4px;
    border: 1px solid {COLOR_TEXT_DIM.name()};
"""

SETTINGS_STATUS_STYLE = f"""
    color: {MATERIAL_GREEN_300.name()};
    font-size: 11px;
    padding: 8px;
    font-weight: 500;
"""

SETTINGS_STATUS_ERROR_STYLE = f"""
    color: {MATERIAL_RED_200.name()};
    font-size: 11px;
    padding: 5px;
"""

SETTINGS_BUTTON_CONTAINER_STYLE = f"""
    QWidget#buttonContainer {{
        background-color: {MATERIAL_SURFACE.name()};
        border-radius: 8px;
        border: 1px solid {COLOR_TEXT_DIM.name()};
    }}
"""

SETTINGS_SYNC_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        border: none;
        border-radius: 4px;
        color: {MATERIAL_PRIMARY.name()};
        padding: 12px 24px;
        font-size: 13px;
        font-weight: 500;
        min-width: 200px;
        text-align: center;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
        padding-top: 13px;
        padding-bottom: 11px;
    }}
"""

SETTINGS_CLOSE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: rgba(255, 255, 255, {ALPHA_DISABLED});
        border: none;
        border-radius: 4px;
        color: {COLOR_TEXT_LIGHT.name()};
        padding: 12px 24px;
        font-size: 13px;
        font-weight: 500;
        min-width: 200px;
        text-align: center;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, {ALPHA_HOVER});
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, {ALPHA_PRESSED});
        padding-top: 13px;
        padding-bottom: 11px;
    }}
"""

DATE_SELECTION_PANE_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BACKGROUND.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 13px;
        padding: 8px;
        background-color: {MATERIAL_SURFACE.name()};
        border-radius: 4px;
    }}
    QTableView {{
        background-color: {MATERIAL_BACKGROUND.name()};
        border: none;
        border-radius: 4px;
        selection-background-color: {MATERIAL_PRIMARY.name()};
        selection-color: {COLOR_BLACK.name()};
        gridline-color: transparent;
    }}
    QTableView::item {{
        padding: 8px;
        border-radius: 2px;
    }}
    QTableView::item:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
    }}
    QTableView::item:selected {{
        background-color: {MATERIAL_PRIMARY.name()};
        color: {COLOR_BLACK.name()};
    }}
    QHeaderView::section {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {MATERIAL_PRIMARY.name()};
        font-weight: bold;
        padding: 8px;
        border: none;
        border-radius: 0px;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 4px;
        border-bottom-left-radius: 4px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }}
    QPushButton {{
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {MATERIAL_PRIMARY.name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        border-bottom: 2px solid {COLOR_TEXT_DIM.name()};
        padding: 8px 24px;
        font-weight: 500;
        min-height: 32px;
        border-radius: 4px;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_ROW_HIGHLIGHT.lighter(110).name()};
        border: 1px solid {COLOR_TEXT_DIM.lighter(110).name()};
        border-bottom: 2px solid {COLOR_TEXT_DIM.lighter(110).name()};
        color: {MATERIAL_PRIMARY.lighter(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_ROW_HIGHLIGHT.darker(110).name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        border-top: 2px solid {COLOR_TEXT_DIM.darker(150).name()};
        border-bottom: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        padding-top: 9px;
        color: {MATERIAL_PRIMARY.name()};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_ROW_HIGHLIGHT.darker(110).name()};
        color: rgba(225, 225, 225, {ALPHA_DISABLED_TEXT});
        border: 1px solid {COLOR_ROW_HIGHLIGHT.name()};
    }}
    QScrollBar:vertical {{
        background-color: {MATERIAL_BACKGROUND.name()};
        width: 12px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {MATERIAL_GREY_800.name()};
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {MATERIAL_GREY_700.name()};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""

# Custom Widget Styles
CUSTOM_TITLE_BAR_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BLUE_GREY_800.name()};
        border: none;
    }}
    QLabel {{
        color: {COLOR_WHITE.name()};
        font-size: 12pt;
        font-weight: bold;
        background-color: transparent;
    }}
    QPushButton {{
        background-color: transparent;
        border: none;
        color: {COLOR_WHITE.name()};
        padding: 5px;
        min-width: 40px;
        max-width: 40px;
        font-size: 16pt;
        font-family: Arial;
    }}
    QPushButton:hover {{ background-color: {MATERIAL_BLUE_GREY_700.name()}; }}
"""

CUSTOM_PROGRESS_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_WHITE.name()};
    }}
    QProgressBar {{
        border: 1px solid {MATERIAL_BLUE_GREY_800.name()};
        border-radius: 2px;
        text-align: center;
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        height: 20px;
    }}
    QProgressBar::chunk {{
        background-color: {MATERIAL_PRIMARY.lighter(120).name()};
        border-radius: 1px;
    }}
    QLabel {{
        color: {COLOR_WHITE.name()};
        font-size: 11px;
        margin-bottom: 5px;
    }}
    QPushButton {{
        background-color: rgba(255, 255, 255, {ALPHA_DISABLED});
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid rgba(255, 255, 255, {ALPHA_HOVER});
        border-radius: 4px;
        padding: 8px 24px;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 120px;
        margin: 8px 0px;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        border: 1px solid {MATERIAL_PRIMARY.name()};
        color: {MATERIAL_PRIMARY.name()};
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
        padding-top: 9px;
        padding-bottom: 7px;
    }}
    QPushButton:disabled {{
        background-color: rgba(255, 255, 255, {ALPHA_DISABLED});
        color: rgba(255, 255, 255, {ALPHA_DISABLED_TEXT});
        border: 1px solid rgba(255, 255, 255, {ALPHA_DISABLED});
    }}
"""

CUSTOM_MESSAGE_BOX_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_WHITE.name()};
    }}
    QLabel {{
        color: {COLOR_WHITE.name()};
        font-size: 11px;
    }}
    QPushButton {{
        background-color: {MATERIAL_PRIMARY.lighter(120).name()};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLOR_WHITE.name()};
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_PRIMARY.lighter(130).name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_PRIMARY.lighter(110).name()};
    }}
"""

CUSTOM_WARNING_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
    }}
    QPushButton {{
        background-color: {MATERIAL_PRIMARY.name()};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLOR_BLACK.name()};
        min-width: 80px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_PRIMARY.darker(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_PRIMARY.darker(120).name()};
    }}
"""

CUSTOM_INFO_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
    }}
    QPushButton {{
        background-color: {MATERIAL_PRIMARY.name()};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLOR_BLACK.name()};
        min-width: 80px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_PRIMARY.darker(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_PRIMARY.darker(120).name()};
    }}
"""

CUSTOM_NOTIFICATION_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
    }}
    QPushButton {{
        background-color: {MATERIAL_PRIMARY.name()};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLOR_BLACK.name()};
        min-width: 80px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_PRIMARY.darker(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_PRIMARY.darker(120).name()};
    }}
"""

CONFIRM_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
    }}
    QPushButton {{
        background-color: {MATERIAL_PRIMARY.name()};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLOR_BLACK.name()};
        min-width: 80px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_PRIMARY.darker(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_PRIMARY.darker(120).name()};
    }}
"""

NEW_CARRIERS_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        padding: 4px;
    }}
    QCheckBox {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        padding: 4px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {MATERIAL_PRIMARY.name()};
        border-radius: 4px;
        background-color: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {MATERIAL_PRIMARY.name()};
        image: url(resources/check.png);
    }}
    QPushButton {{
        background-color: {MATERIAL_PRIMARY.name()};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: {COLOR_BLACK.name()};
        min-width: 100px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {MATERIAL_PRIMARY.darker(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_PRIMARY.darker(120).name()};
    }}
    QPushButton#secondary {{
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {MATERIAL_PRIMARY.name()};
        border: 1px solid {MATERIAL_PRIMARY.name()};
    }}
    QPushButton#secondary:hover {{
        background-color: {COLOR_ROW_HIGHLIGHT.lighter(110).name()};
    }}
    QPushButton#secondary:pressed {{
        background-color: {COLOR_ROW_HIGHLIGHT.darker(110).name()};
    }}
"""

# Clean Moves Dialog Styles
CLEAN_MOVES_DIALOG_STYLE = f"""
    QDialog {{
        background-color: {MATERIAL_BACKGROUND.name()};
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QTableWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        alternate-background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
        gridline-color: {COLOR_TEXT_DIM.name()};
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QTableWidget::item:selected {{
        background-color: {MATERIAL_PRIMARY_VARIANT.name()};
        color: {COLOR_WHITE.name()};
    }}
    QHeaderView::section {{
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        padding: 5px;
        border: 1px solid {COLOR_TEXT_DIM.name()};
    }}
    QPushButton {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        color: {MATERIAL_PRIMARY.name()};
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
    }}
    QPushButton:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_DIM.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
    }}
"""

SPLIT_MOVE_DIALOG_STYLE = f"""
    QDialog {{
        background-color: {MATERIAL_BACKGROUND.name()};
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QGroupBox {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
        border-radius: 4px;
        padding: 15px;
        margin-top: 15px;
    }}
    QGroupBox::title {{
        color: {MATERIAL_PRIMARY.name()};
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    QLineEdit {{
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
        padding: 5px;
        border-radius: 4px;
    }}
    QLineEdit:focus {{
        border: 1px solid {MATERIAL_PRIMARY.name()};
    }}
    QLineEdit:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_DIM.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
    }}
    QPushButton {{
        background-color: rgba(187, 134, 252, {ALPHA_HOVER});
        color: {MATERIAL_PRIMARY.name()};
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
    }}
    QPushButton:pressed {{
        background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
    }}
    QPushButton:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_DIM.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
    }}
"""

CLEAN_MOVES_SAVE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_ROW_HIGHLIGHT.name()};
        color: {MATERIAL_PRIMARY.name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        border-bottom: 2px solid {COLOR_TEXT_DIM.name()};
        padding: 8px 24px;
        font-weight: 500;
        min-height: 32px;
        border-radius: 4px;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_ROW_HIGHLIGHT.lighter(110).name()};
        border: 1px solid {COLOR_TEXT_DIM.lighter(110).name()};
        border-bottom: 2px solid {COLOR_TEXT_DIM.lighter(110).name()};
        color: {MATERIAL_PRIMARY.lighter(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_ROW_HIGHLIGHT.darker(110).name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        border-top: 2px solid {COLOR_TEXT_DIM.darker(150).name()};
        border-bottom: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
        padding-top: 9px;
        color: {MATERIAL_PRIMARY.name()};
    }}
    QPushButton:disabled {{
        background-color: {COLOR_ROW_HIGHLIGHT.darker(110).name()};
        color: {COLOR_TEXT_DIM.name()};
        border: 1px solid {COLOR_ROW_HIGHLIGHT.name()};
    }}
"""

CLEAN_MOVES_CANCEL_BUTTON_STYLE = CLEAN_MOVES_SAVE_BUTTON_STYLE

DISABLED_START_INPUT_STYLE = f"""
    QLineEdit:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_DIM.lighter(150).name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
    }}
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
        f"""
        QMainWindow, QDialog {{
            background-color: {MATERIAL_BACKGROUND.name()};
        }}
        QWidget {{
            font-family: Roboto, Arial, sans-serif;
        }}
        QPushButton {{
            background-color: rgba(187, 134, 252, {ALPHA_HOVER});
            border: none;
            color: {MATERIAL_PRIMARY.name()};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: normal;
        }}
        QPushButton:hover {{
            background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
        }}
        QPushButton:pressed {{
            background-color: rgba(187, 134, 252, {ALPHA_SELECTED});
        }}
        QPushButton:checked {{
            background-color: {MATERIAL_PRIMARY.name()};
            color: {COLOR_BLACK.name()};
        }}
        QTableView {{
            background-color: {MATERIAL_SURFACE.name()};
            alternate-background-color: {COLOR_ROW_HIGHLIGHT.name()};
            selection-background-color: {MATERIAL_PRIMARY_VARIANT.name()};
            selection-color: {COLOR_WHITE.name()};
            gridline-color: {COLOR_TEXT_DIM.name()};
            border-radius: 4px;
        }}
        QTableView::item {{
            /* Keep minimal styling to not interfere with dynamic colors */
        }}
        QHeaderView::section {{
            background-color: {COLOR_ROW_HIGHLIGHT.name()};
            color: {COLOR_TEXT_LIGHT.name()};
            padding: 4px;
            border: 1px solid {COLOR_TEXT_DIM.name()};
        }}
        QHeaderView::section:first {{
            border-top-left-radius: 4px;
        }}
        QHeaderView::section:last {{
            border-top-right-radius: 4px;
        }}
        QTableCornerButton::section {{
            background-color: {MATERIAL_SURFACE.name()};
            border: none;
        }}
        QTableView::item:focus {{
            border: none;
            outline: none;
        }}
        QTabWidget::pane {{
            border: 1px solid {COLOR_TEXT_DIM.name()};
        }}
        QTabBar::tab {{
            background-color: {MATERIAL_SURFACE.name()};
            color: {COLOR_TEXT_DIM.lighter(150).name()};
            padding: 8px 16px;
            border: 1px solid {COLOR_TEXT_DIM.name()};
        }}
        QTabBar::tab:selected {{
            background-color: {MATERIAL_PRIMARY.name()};
            color: {COLOR_BLACK.name()};
        }}
        QLineEdit {{
            background-color: {COLOR_ROW_HIGHLIGHT.name()};
            color: {COLOR_TEXT_LIGHT.name()};
            border: 1px solid {COLOR_TEXT_DIM.name()};
            padding: 4px;
            border-radius: 4px;
        }}
        QComboBox {{
            background-color: {COLOR_ROW_HIGHLIGHT.name()};
            color: {COLOR_TEXT_LIGHT.name()};
            border: 1px solid {COLOR_TEXT_DIM.name()};
            padding: 4px;
            border-radius: 4px;
        }}
        QScrollBar {{
            background-color: {MATERIAL_SURFACE.name()};
            border: none;
        }}
        QScrollBar:vertical {{
            width: 10px;
        }}
        QScrollBar:horizontal {{
            height: 10px;
        }}
        QScrollBar::handle {{
            background-color: {MATERIAL_GREY_800.name()};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:hover {{
            background-color: {MATERIAL_GREY_700.name()};
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0px;
            height: 0px;
            background: none;
            border: none;
        }}
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none;
        }}
        /* Dialog Styling */
        QDialog {{
            background-color: {MATERIAL_BACKGROUND.name()};
            border: none;
            padding: 1px;
        }}
        QDialog > QWidget {{
            background-color: {MATERIAL_BACKGROUND.name()};
            border: 2px solid {MATERIAL_SURFACE.name()};
            border-bottom: 2px solid {COLOR_ROW_HIGHLIGHT.name()};
        }}
        QDialog QLabel {{
            color: {COLOR_WHITE.name()};
        }}
        QDialog QPushButton {{
            min-width: 250px;
        }}
        /* Top Button Row Styling */
        QWidget#ButtonContainer {{
            background-color: {MATERIAL_SURFACE.name()};
            border-bottom: 1px solid {COLOR_TEXT_DIM.name()};
        }}
        QWidget#ButtonContainer QPushButton {{
            background-color: transparent;
            border: none;
            color: {COLOR_TEXT_LIGHT.name()};
            padding: 12px 24px;
            font-size: 13px;
            font-weight: normal;
            text-align: left;
        }}
        QWidget#ButtonContainer QPushButton:hover {{
            background-color: {COLOR_ROW_HIGHLIGHT.name()};
        }}
        QWidget#ButtonContainer QPushButton:pressed,
        QWidget#ButtonContainer QPushButton:checked {{
            background-color: {MATERIAL_PRIMARY.name()};
            color: {COLOR_BLACK.name()};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_ROW_HIGHLIGHT.darker(110).name()};
            color: rgba(225, 225, 225, {ALPHA_DISABLED_TEXT});
            border: 1px solid {COLOR_ROW_HIGHLIGHT.name()};
        }}
    """
    )


def calculate_optimal_gray(bg_color, target_ratio=7.0):
    """Calculate optimal gray value for given background color"""
    if bg_color is None:
        bg_color = MATERIAL_BACKGROUND  # Use theme constant instead of hardcoded value

    bg_luminance = (
        0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
    ) / 255

    # Binary search for optimal gray value
    left, right = 0, 255
    best_gray = 0
    best_diff = float("inf")

    while left <= right:
        gray = (left + right) // 2
        gray_luminance = gray / 255

        # Calculate contrast ratio
        lighter = max(gray_luminance, bg_luminance) + 0.05
        darker = min(gray_luminance, bg_luminance) + 0.05
        ratio = lighter / darker

        diff = abs(ratio - target_ratio)
        if diff < best_diff:
            best_diff = diff
            best_gray = gray

        if ratio < target_ratio:
            # For dark backgrounds, prefer lighter text
            if bg_luminance < 0.5:
                left = gray + 1
            # For light backgrounds, prefer darker text
            else:
                right = gray - 1
        else:
            if bg_luminance < 0.5:
                right = gray - 1
            else:
                left = gray + 1

    return QColor(best_gray, best_gray, best_gray)
