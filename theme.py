# theme.py
"""Application theming and style management.

This module defines the application's visual theme and styling using Material Design dark theme
principles. All colors and styles are centralized here to ensure consistency across the application.

Color System:
    The theme uses a Material Design dark theme color system with these key components:
    - Primary: Purple (#BB86FC) - Main brand color used for key UI elements
    - Secondary: Teal (#03DAC6) - Accent color for secondary actions
    - Background: Dark (#121212) - Main app background
    - Surface: Slightly lighter (#1E1E1E) - Elevated surface colors
    - Error: Pink-red (#CF6679) - Error states and warnings

State Management:
    UI element states are handled through alpha values:
    - ALPHA_HOVER (0.1) - Hover state transparency
    - ALPHA_PRESSED (0.15) - Pressed state transparency
    - ALPHA_SELECTED (0.2) - Selected state transparency
    - ALPHA_DISABLED (0.05) - Disabled state transparency
    - ALPHA_DISABLED_TEXT (0.3) - Disabled text transparency

Color Categories:
    - Material Colors: Core theme colors (MATERIAL_*)
    - Status Colors: Carrier list status indicators (COLOR_STATUS_*)
    - UI Colors: Interface elements (COLOR_TEXT_*, COLOR_BG_*)
    - Semantic Colors: Success/error states (COLOR_MAXIMIZED_*)
    - Feature Colors: Violation-specific colors (COLOR_VIOLATION_*)

Style Definitions:
    Component styles are defined as formatted strings using the color constants.
    This ensures consistent styling across all widgets while allowing for
    dynamic color updates.

Note:
    When adding new colors or styles:
    1. Use semantic naming that describes the color's purpose
    2. Group related colors together in the appropriate section
    3. Add clear comments explaining the color's usage
    4. Consider accessibility with sufficient contrast ratios
    5. Maintain consistency with the Material Design spec
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QStyleFactory,
)


# Helper functions for color manipulation
def rgba(rgb: tuple[int, int, int], alpha: float) -> str:
    """Create an rgba string from RGB values and alpha."""
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"


def rgb_str(rgb_tuple):
    """Convert RGB tuple to CSS rgb() string.

    Args:
        rgb_tuple (tuple): RGB color values as (r,g,b)

    Returns:
        str: CSS rgb() string
    """
    return f"rgb({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]})"


# Material Design color palette
RGB_BASE = (25, 23, 36)  # Base color
RGB_SURFACE = (33, 32, 46)  # Surface color
RGB_OVERLAY = (41, 40, 55)  # Overlay color
RGB_MUTED = (110, 106, 134)  # Muted text
RGB_SUBTLE = (144, 140, 170)  # Subtle accents
RGB_TEXT = (224, 222, 244)  # Main text
RGB_LOVE = (235, 111, 146)  # Love/Error
RGB_GOLD = (246, 193, 119)  # Gold/Warning
RGB_ROSE = (235, 188, 186)  # Rose/Info
RGB_PINE = (49, 116, 143)  # Pine/Success
RGB_FOAM = (156, 207, 216)  # Foam/Link
RGB_IRIS = (196, 167, 231)  # Iris/Primary

# Highlight colors
RGB_HIGHLIGHT_LOW = (33, 32, 46)  # Highlight Low - #21202e
RGB_HIGHLIGHT_MED = (64, 61, 82)  # Highlight Med - #403d52
RGB_HIGHLIGHT_HIGH = (82, 79, 103)  # Highlight High - #524f67

# Material Design color constants
MATERIAL_SURFACE = rgb_str(RGB_SURFACE)
MATERIAL_PRIMARY = rgb_str(RGB_IRIS)
MATERIAL_SECONDARY = rgb_str(RGB_PINE)
MATERIAL_BACKGROUND = rgb_str(RGB_BASE)
MATERIAL_PRIMARY_LIGHT = rgb_str(RGB_FOAM)
MATERIAL_PRIMARY_DARK = rgb_str(RGB_PINE)
MATERIAL_RED_800 = rgb_str(RGB_LOVE)
MATERIAL_RED_900 = rgb_str((187, 89, 117))
MATERIAL_RED_200 = rgb_str((242, 153, 179))
COLOR_TEXT_LIGHT = rgb_str(RGB_TEXT)
COLOR_TEXT_DIM = rgb_str(RGB_MUTED)
COLOR_BLACK = "rgb(0, 0, 0)"
COLOR_ROW_HIGHLIGHT = rgb_str(RGB_HIGHLIGHT_LOW)
COLOR_STATUS_NL = rgb_str(RGB_PINE)
COLOR_STATUS_PTF = rgb_str(RGB_FOAM)

# Alpha values for UI state management
ALPHA_DISABLED = 0.08  # More subtle disabled state
ALPHA_HOVER = 0.12  # Softer hover effect
ALPHA_PRESSED = 0.16  # Gentle pressed state
ALPHA_SELECTED = 0.20  # Subtle selected state
ALPHA_DISABLED_TEXT = 0.38  # Improved disabled text contrast

# Base colors for Material Design Dark Theme
MATERIAL_BACKGROUND = QColor(*RGB_BASE)  # Main background
MATERIAL_SURFACE = QColor(*RGB_SURFACE)  # Surface color
MATERIAL_PRIMARY = QColor(*RGB_IRIS)  # Primary color
MATERIAL_PRIMARY_LIGHT = QColor(*RGB_IRIS).lighter(115)  # Lighter primary
MATERIAL_PRIMARY_DARK = QColor(*RGB_IRIS).darker(110)  # Darker primary
MATERIAL_RED_800 = QColor(*RGB_LOVE).lighter(115)  # Error hover
MATERIAL_RED_900 = QColor(*RGB_LOVE)  # Error base
MATERIAL_RED_200 = QColor(*RGB_LOVE).lighter(140)  # Error text
COLOR_TEXT_LIGHT = QColor(*RGB_TEXT)  # Main text
COLOR_TEXT_DIM = QColor(*RGB_MUTED)  # Dimmed text using Muted
COLOR_BG_HOVER = QColor(*RGB_HIGHLIGHT_LOW)  # Hover background

# Common highlight colors
HIGHLIGHT_MED = rgba(RGB_HIGHLIGHT_MED, 1.0)
HIGHLIGHT_HIGH = rgba(RGB_HIGHLIGHT_HIGH, 1.0)

# Common button style with variants
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BG_HOVER.name()};
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QPushButton:pressed {{
        background-color: {MATERIAL_BACKGROUND.name()};
        border: 1px solid {COLOR_BG_HOVER.name()};
    }}
    QPushButton:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_DIM.name()};
        border: 1px solid {COLOR_TEXT_DIM.name()};
    }}
    QPushButton[objectName="primary"] {{
        background-color: {rgba(RGB_IRIS, 0.15)};
        color: {QColor(*RGB_IRIS).name()};
        border: 2px solid {rgba(RGB_IRIS, 0.5)};
        border-radius: 6px;
    }}
    QPushButton[objectName="primary"]:hover {{
        background-color: {rgba(RGB_IRIS, 0.25)};
        border: 2px solid {QColor(*RGB_IRIS).name()};
        color: {QColor(*RGB_IRIS).lighter(115).name()};
    }}
    QPushButton[objectName="primary"]:pressed {{
        background-color: {rgba(RGB_IRIS, 0.35)};
        border: 2px solid {QColor(*RGB_IRIS).darker(110).name()};
        color: {QColor(*RGB_IRIS).darker(110).name()};
    }}
    QPushButton[objectName="destructive"] {{
        background-color: {QColor(*RGB_LOVE).name()};
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QPushButton[objectName="destructive"]:hover {{
        background-color: {QColor(*RGB_LOVE).lighter(115).name()};
    }}
    QPushButton[objectName="destructive"]:pressed {{
        background-color: {QColor(*RGB_LOVE).darker(110).name()};
    }}
    QPushButton[objectName="secondary"] {{
        background-color: transparent;
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
    }}
    QPushButton[objectName="secondary"]:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.15)};
        color: {QColor(*RGB_IRIS).name()};
        border: 1px solid {QColor(*RGB_IRIS).name()};
    }}
    QPushButton[objectName="secondary"]:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.25)};
    }}
"""


def calculate_optimal_gray(bg_color, target_ratio=7.0):
    """Calculate optimal gray value for given background color"""
    if bg_color is None:
        bg_color = MATERIAL_BACKGROUND

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
            if bg_luminance < 0.5:
                left = gray + 1
            else:
                right = gray - 1
        else:
            if bg_luminance < 0.5:
                right = gray - 1
            else:
                left = gray + 1

    return QColor(best_gray, best_gray, best_gray)


# Rosé Pine Color Palette - Official values from rosepinetheme.com
# Base colors
RGB_BASE = (25, 23, 36)  # Base - #191724
RGB_SURFACE = (31, 29, 46)  # Surface - #1f1d2e
RGB_OVERLAY = (38, 35, 58)  # Overlay - #26233a
RGB_MUTED = (110, 106, 134)  # Muted - #6e6a86
RGB_SUBTLE = (144, 140, 170)  # Subtle - #908caa
RGB_TEXT = (224, 222, 244)  # Text - #e0def4

# Accent colors
RGB_LOVE = (235, 111, 146)  # Love - #eb6f92
RGB_GOLD = (246, 193, 119)  # Gold - #f6c177
RGB_ROSE = (235, 188, 186)  # Rose - #ebbcba
RGB_PINE = (49, 116, 143)  # Pine - #31748f
RGB_FOAM = (156, 207, 216)  # Foam - #9ccfd8
RGB_IRIS = (196, 167, 231)  # Iris - #c4a7e7

# Highlight colors
RGB_HIGHLIGHT_LOW = (33, 32, 46)  # Highlight Low - #21202e
RGB_HIGHLIGHT_MED = (64, 61, 82)  # Highlight Med - #403d52
RGB_HIGHLIGHT_HIGH = (82, 79, 103)  # Highlight High - #524f67


def rgba(rgb: tuple[int, int, int], alpha: float) -> str:
    """Create an rgba string from RGB values and alpha."""
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"


def rgb_str(rgb: tuple[int, int, int]) -> str:
    """Create an rgb string from RGB values."""
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


# Alpha values for UI state management
ALPHA_DISABLED = 0.08  # More subtle disabled state
ALPHA_HOVER = 0.12  # Softer hover effect
ALPHA_PRESSED = 0.16  # Gentle pressed state
ALPHA_SELECTED = 0.20  # Subtle selected state
ALPHA_DISABLED_TEXT = 0.38  # Improved disabled text contrast

# Material Design Dark Theme - Core Colors using Rosé Pine
MATERIAL_PRIMARY = QColor(*RGB_IRIS)  # Primary brand color (Iris)
MATERIAL_PRIMARY_LIGHT = QColor(*RGB_IRIS).lighter(115)  # Lighter primary
MATERIAL_PRIMARY_DARK = QColor(*RGB_IRIS).darker(110)  # Darker primary
MATERIAL_SECONDARY = QColor(*RGB_PINE)  # Accent color (Pine)
MATERIAL_BACKGROUND = QColor(*RGB_BASE)  # Main background
MATERIAL_SURFACE = QColor(*RGB_SURFACE)  # Surface color
MATERIAL_ERROR = QColor(*RGB_LOVE)  # Error states (Love)

# Additional Material Colors
MATERIAL_BLUE_GREY_800 = QColor(*RGB_HIGHLIGHT_MED)  # Header backgrounds
MATERIAL_BLUE_GREY_900 = QColor(*RGB_HIGHLIGHT_LOW)  # Day name backgrounds
MATERIAL_RED_900 = QColor(*RGB_LOVE)  # Error states
MATERIAL_RED_200 = QColor(*RGB_LOVE)  # Error text
MATERIAL_GREEN_900 = QColor(*RGB_FOAM)  # Success states
MATERIAL_GREEN_300 = QColor(*RGB_FOAM)  # Success text
MATERIAL_GREY_600 = QColor(*RGB_MUTED)  # Dot color
MATERIAL_GREY_700 = QColor(*RGB_SUBTLE)  # Hover color
MATERIAL_GREY_800 = QColor(*RGB_HIGHLIGHT_MED)  # Checkbox unchecked
MATERIAL_BLUE_600 = QColor(*RGB_PINE)  # Checkbox checked
MATERIAL_BLUE_GREY_700 = QColor(*RGB_HIGHLIGHT_HIGH)  # Title bar hover
MATERIAL_RED_700 = QColor(*RGB_LOVE)  # Close button hover

# Basic Colors
COLOR_BLACK = QColor(26, 24, 38)  # Darker base for contrast
COLOR_WHITE = QColor(*RGB_TEXT)  # Pure white for text
COLOR_TRANSPARENT = Qt.transparent  # Transparent color for clearing backgrounds

# Application-specific Colors
COLOR_ROW_HIGHLIGHT = QColor(*RGB_HIGHLIGHT_LOW)  # Subtle row highlighting
COLOR_CELL_HIGHLIGHT = MATERIAL_PRIMARY.darker(150)  # Selected cell
COLOR_WEEKLY_REMEDY = MATERIAL_SECONDARY.darker(150)  # Weekly totals
COLOR_NO_HIGHLIGHT = MATERIAL_SURFACE  # Default state
COLOR_TEXT_LIGHT = QColor(*RGB_TEXT)  # Main text color
COLOR_TEXT_DIM = QColor(*RGB_MUTED)  # Dimmed text using Muted
COLOR_MAXIMIZED_TRUE = QColor(*RGB_FOAM)  # Success state
COLOR_MAXIMIZED_FALSE = QColor(*RGB_LOVE)  # Error state

# Violation-specific Colors
COLOR_VIOLATION = QColor(*RGB_IRIS).darker(110)  # Darker purple for violations
COLOR_VIOLATION_SUMMARY = QColor(*RGB_IRIS).lighter(
    130
)  # Light purple for summary rows
COLOR_VIOLATION_WEEKLY = QColor(*RGB_PINE)  # Pine (teal) for weekly totals
COLOR_VIOLATION_BACKGROUND = QColor(
    *RGB_HIGHLIGHT_LOW
)  # Subtle background for violation rows

# Update the existing violation colors section to use these
VIOLATION_MODEL_COLORS = {
    "violation": COLOR_VIOLATION,
    "summary": COLOR_VIOLATION_SUMMARY,
    "weekly": COLOR_VIOLATION_WEEKLY,
    "background": COLOR_VIOLATION_BACKGROUND,
}

# Status-specific Colors
COLOR_STATUS_OTDL = QColor(*RGB_PINE).lighter(120)  # Brightened for better visibility
COLOR_STATUS_WAL = QColor(*RGB_IRIS).lighter(120)  # Brightened for better visibility
COLOR_STATUS_NL = QColor(*RGB_FOAM).lighter(110)  # Slightly brightened
COLOR_STATUS_PTF = QColor(*RGB_ROSE).lighter(110)  # Slightly brightened

# Background Colors
COLOR_BG_DARKER = QColor(*RGB_BASE).darker(110)  # Darker background
COLOR_BG_DARK = QColor(*RGB_SURFACE)  # Dark background
COLOR_BG_HOVER = QColor(*RGB_HIGHLIGHT_LOW)  # Hover background

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
        border-bottom: 1px solid {QColor(*RGB_HIGHLIGHT_LOW).name()};
    }}
    {BUTTON_STYLE}
    QPushButton {{
        padding: 16px 32px;
        font-size: 14px;
        margin: 12px 6px;
        min-width: 180px;
        text-transform: uppercase;
    }}
"""

FILTER_BUTTON_ROW_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BACKGROUND.name()};
        border-top: 1px solid {QColor(*RGB_HIGHLIGHT_LOW).name()};
    }}
    {BUTTON_STYLE}
    QPushButton {{
        padding: 4px 12px;
        font-size: 11px;
        margin: 4px;
        min-width: 90px;
        max-height: 24px;
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
        background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.7)};
        color: {rgba(RGB_TEXT, ALPHA_DISABLED_TEXT)};
        padding: 10px 24px;
        border: none;
        border-right: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
        min-width: 100px;
        font: 12px;
        font-weight: 500;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        color: {QColor(*RGB_IRIS).name()};
        background-color: {MATERIAL_SURFACE.name()};
        border-top: 2px solid {QColor(*RGB_IRIS).name()};
        border-right: 1px solid {QColor(*RGB_HIGHLIGHT_HIGH).name()};
        border-left: 1px solid {QColor(*RGB_HIGHLIGHT_HIGH).name()};
        padding-top: 8px;
    }}
    QTabBar::tab:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        color: {QColor(*RGB_IRIS).lighter(110).name()};
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
        color: {rgba(RGB_TEXT, ALPHA_DISABLED_TEXT)};
        padding: 4px 8px;
        margin: 0;
        border-right: 1px solid {QColor(*RGB_HIGHLIGHT_LOW).name()};
        font-size: 10px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1px;
        width: 85px;
    }}
    QTabBar::tab:first {{
        margin-left: 5px;
    }}
    QTabBar::tab:last {{
        margin-right: 0px;
    }}
    QTabBar::tab:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_HOVER)};
        color: {QColor(*RGB_IRIS).lighter(110).name()};
    }}
    QTabBar::tab:selected {{
        color: {QColor(*RGB_IRIS).name()};
        border-bottom: 2px solid {QColor(*RGB_IRIS).name()};
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_PRESSED)};
        border-right: 1px solid {QColor(*RGB_IRIS).name()};
    }}
    QTabBar::scroller {{
        width: 0px;
    }}
    QTabWidget::tab-bar {{
        alignment: left;
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
        background-color: {rgba(RGB_IRIS, ALPHA_HOVER)};
        border: none;
        border-radius: 4px;
        color: {MATERIAL_PRIMARY.name()};
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        min-width: 120px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_IRIS, ALPHA_PRESSED)};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_IRIS, ALPHA_SELECTED)};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
    }}
"""

SETTINGS_PATH_DISPLAY_STYLE = f"""
    color: {MATERIAL_PRIMARY.lighter(120).name()};
    font-size: 11px;
    padding: 8px;
    background-color: {rgba((30, 30, 30), ALPHA_DISABLED_TEXT)};
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
    {BUTTON_STYLE}
    QPushButton {{
        padding: 12px 24px;
        font-size: 13px;
        min-width: 200px;
    }}
"""

SETTINGS_CLOSE_BUTTON_STYLE = f"""
    {BUTTON_STYLE}
    QPushButton {{
        padding: 12px 24px;
        font-size: 13px;
        min-width: 200px;
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
        background-color: {rgba(RGB_IRIS, ALPHA_HOVER)};
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
        color: {rgba(RGB_TEXT, ALPHA_DISABLED_TEXT)};
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
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QProgressBar {{
        border: 1px solid {QColor(*RGB_IRIS).name()};
        border-radius: 4px;
        text-align: center;
        background-color: {QColor(*RGB_HIGHLIGHT_LOW).darker(120).name()};
        height: 20px;
        margin: 8px 0px;
    }}
    QProgressBar::chunk {{
        background-color: {QColor(*RGB_IRIS).lighter(110).name()};
        border-radius: 3px;
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        margin: 8px 0px;
    }}
    QPushButton {{
        background-color: {rgba(RGB_LOVE, 0.15)};
        color: {QColor(*RGB_LOVE).lighter(120).name()};
        border: 1px solid {QColor(*RGB_LOVE).name()};
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
        background-color: {rgba(RGB_LOVE, 0.25)};
        border: 1px solid {QColor(*RGB_LOVE).lighter(110).name()};
        color: {QColor(*RGB_LOVE).lighter(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_LOVE, 0.35)};
        padding-top: 9px;
        padding-bottom: 7px;
        color: {QColor(*RGB_LOVE).name()};
    }}
"""

CUSTOM_MESSAGE_BOX_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_LIGHT.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        padding: 8px;
        line-height: 1.4;
        qproperty-wordWrap: true;
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        border: 1px solid {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        border-radius: 4px;
        padding: 8px 16px;
        margin: 8px;
        color: {COLOR_TEXT_LIGHT.name()};
        min-width: 80px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        border: 1px solid {QColor(*RGB_IRIS).name()};
        color: {QColor(*RGB_IRIS).lighter(110).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, ALPHA_PRESSED)};
        color: {QColor(*RGB_IRIS).name()};
    }}
"""

CUSTOM_WARNING_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        line-height: 1.4;
    }}
    QLabel#iconLabel {{
        padding: 8px;
        background-color: transparent;
    }}
    QLabel#messageLabel {{
        padding: 8px;
        font-size: 12px;
        line-height: 1.6;
        qproperty-wordWrap: true;
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        border: 1px solid {rgba(RGB_LOVE, ALPHA_HOVER)};
        border-radius: 4px;
        padding: 8px 16px;
        margin: 8px;
        color: {QColor(*RGB_LOVE).lighter(110).name()};
        min-width: 80px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        border: 1px solid {QColor(*RGB_LOVE).name()};
        color: {QColor(*RGB_LOVE).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, ALPHA_PRESSED)};
        color: {QColor(*RGB_LOVE).darker(110).name()};
    }}
"""

CUSTOM_INFO_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        line-height: 1.4;
    }}
    QLabel#iconLabel {{
        padding: 8px;
        background-color: transparent;
    }}
    QLabel#messageLabel {{
        padding: 8px;
        font-size: 12px;
        line-height: 1.6;
        qproperty-wordWrap: true;
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        border: 1px solid {rgba(RGB_PINE, ALPHA_HOVER)};
        border-radius: 4px;
        padding: 8px 16px;
        margin: 8px;
        color: {QColor(*RGB_PINE).lighter(110).name()};
        min-width: 80px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        border: 1px solid {QColor(*RGB_PINE).name()};
        color: {QColor(*RGB_PINE).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, ALPHA_PRESSED)};
        color: {QColor(*RGB_PINE).darker(110).name()};
    }}
"""

CUSTOM_NOTIFICATION_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        line-height: 1.4;
    }}
    QLabel#iconLabel {{
        padding: 8px;
        background-color: transparent;
    }}
    QLabel#messageLabel {{
        padding: 8px;
        font-size: 12px;
        line-height: 1.6;
        qproperty-wordWrap: true;
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        border: 1px solid {rgba(RGB_FOAM, ALPHA_HOVER)};
        border-radius: 4px;
        padding: 8px 16px;
        margin: 8px;
        color: {QColor(*RGB_FOAM).lighter(110).name()};
        min-width: 80px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        border: 1px solid {QColor(*RGB_FOAM).name()};
        color: {QColor(*RGB_FOAM).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, ALPHA_PRESSED)};
        color: {QColor(*RGB_FOAM).darker(110).name()};
    }}
"""

CONFIRM_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_SURFACE.name()};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        line-height: 1.4;
    }}
    QLabel#iconLabel {{
        padding: 8px;
        background-color: transparent;
    }}
    QLabel#messageLabel {{
        padding: 8px;
        font-size: 12px;
        line-height: 1.6;
        qproperty-wordWrap: true;
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        border: 1px solid {rgba(RGB_GOLD, ALPHA_HOVER)};
        border-radius: 4px;
        padding: 8px 16px;
        margin: 8px;
        color: {QColor(*RGB_GOLD).lighter(110).name()};
        min-width: 80px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, ALPHA_HOVER)};
        border: 1px solid {QColor(*RGB_GOLD).name()};
        color: {QColor(*RGB_GOLD).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, ALPHA_PRESSED)};
        color: {QColor(*RGB_GOLD).darker(110).name()};
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
        alternate-background-color: {QColor(*RGB_HIGHLIGHT_LOW).name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
        gridline-color: {QColor(*RGB_HIGHLIGHT_LOW).name()};
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QTableWidget::item:selected {{
        background-color: {QColor(*RGB_IRIS).name()};
        color: {COLOR_BLACK.name()};
    }}
    QTableWidget::item:selected:focus {{
        background-color: {QColor(*RGB_IRIS).lighter(110).name()};
        color: {COLOR_BLACK.name()};
    }}
    QHeaderView::section {{
        background-color: {QColor(*RGB_HIGHLIGHT_LOW).name()};
        color: {COLOR_TEXT_LIGHT.name()};
        padding: 5px;
        border: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.7)};
        color: {QColor(*RGB_IRIS).name()};
        border: 1px solid {QColor(*RGB_IRIS).name()};
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
        letter-spacing: 0.5px;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, 0.8)};
        border: 1px solid {QColor(*RGB_IRIS).lighter(115).name()};
        color: {QColor(*RGB_IRIS).lighter(115).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, 0.9)};
        border: 1px solid {QColor(*RGB_IRIS).darker(110).name()};
        color: {QColor(*RGB_IRIS).darker(110).name()};
    }}
    QPushButton:disabled {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        color: {rgba(RGB_TEXT, ALPHA_DISABLED_TEXT)};
        border: 1px solid {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        padding: 4px;
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
        border: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
        border-radius: 4px;
        padding: 15px;
        margin-top: 15px;
    }}
    QGroupBox::title {{
        color: {QColor(*RGB_IRIS).name()};
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    QLineEdit {{
        background-color: {QColor(*RGB_HIGHLIGHT_LOW).name()};
        color: {COLOR_TEXT_LIGHT.name()};
        border: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
        padding: 5px;
        border-radius: 4px;
    }}
    QLineEdit:focus {{
        border: 1px solid {QColor(*RGB_IRIS).name()};
    }}
    QLineEdit:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {rgba(RGB_TEXT, ALPHA_DISABLED_TEXT)};
        border: 1px solid {QColor(*RGB_HIGHLIGHT_LOW).name()};
    }}
    QPushButton {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.7)};
        color: {QColor(*RGB_IRIS).name()};
        border: 1px solid {QColor(*RGB_IRIS).name()};
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
        letter-spacing: 0.5px;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {rgba(RGB_HIGHLIGHT_MED, 0.8)};
        border: 1px solid {QColor(*RGB_IRIS).lighter(115).name()};
        color: {QColor(*RGB_IRIS).lighter(115).name()};
    }}
    QPushButton:pressed {{
        background-color: {rgba(RGB_HIGHLIGHT_HIGH, 0.9)};
        border: 1px solid {QColor(*RGB_IRIS).darker(110).name()};
        color: {QColor(*RGB_IRIS).darker(110).name()};
    }}
    QPushButton:disabled {{
        background-color: {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
        color: {rgba(RGB_TEXT, ALPHA_DISABLED_TEXT)};
        border: 1px solid {rgba(RGB_HIGHLIGHT_LOW, ALPHA_DISABLED)};
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        padding: 4px;
    }}
"""

CLEAN_MOVES_SAVE_BUTTON_STYLE = f"""
    {BUTTON_STYLE}
    QPushButton {{
        padding: 8px 24px;
        min-height: 32px;
        font-size: 14px;
        text-transform: uppercase;
    }}
"""

CLEAN_MOVES_CANCEL_BUTTON_STYLE = f"""
    {BUTTON_STYLE}
    QPushButton {{
        padding: 8px 24px;
        min-height: 32px;
        font-size: 14px;
        text-transform: uppercase;
    }}
"""

DISABLED_START_INPUT_STYLE = f"""
    QLineEdit:disabled {{
        background-color: {MATERIAL_SURFACE.name()};
        color: {COLOR_TEXT_DIM.lighter(150).name()};
        border: 1px solid {COLOR_TEXT_DIM.darker(110).name()};
    }}
"""

# OTDL Maximization Styles
OTDL_TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {MATERIAL_SURFACE.name()};
        alternate-background-color: {QColor(*RGB_HIGHLIGHT_LOW).name()};
        border: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
        gridline-color: {QColor(*RGB_HIGHLIGHT_MED).name()};
        border-radius: 4px;
    }}
    QTableWidget::item {{
        min-height: 35px;
        padding: 2px;
    }}
    QTableWidget::item:selected {{
        background-color: {QColor(*RGB_IRIS).name()};
        color: {COLOR_BLACK.name()};
    }}
    QHeaderView::section {{
        background-color: {MATERIAL_BLUE_GREY_800.name()};
        color: {COLOR_TEXT_LIGHT.name()};
        padding: 8px;
        border: 1px solid {QColor(*RGB_HIGHLIGHT_MED).name()};
        font-weight: bold;
        min-height: 15px;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 4px;
        border-bottom-left-radius: 4px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }}
"""

OTDL_CHECKBOX_STYLE = f"""
    QCheckBox {{
        spacing: 4px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {MATERIAL_PRIMARY.name()};
        border-radius: 3px;
        background-color: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {MATERIAL_PRIMARY.name()};
        image: url(resources/check.png);
    }}
    QCheckBox::indicator:hover {{
        border: 1px solid {MATERIAL_PRIMARY.lighter(110).name()};
    }}
"""

OTDL_CELL_WIDGET_STYLE = (
    lambda row_color: f"""
    QWidget {{
        background-color: {rgba(RGB_FOAM, ALPHA_HOVER)};
        padding: 2px;
        margin: 0px;
    }}
    QCheckBox {{
        background-color: {rgba(RGB_FOAM, ALPHA_HOVER)};
        padding: 2px;
        spacing: 4px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {MATERIAL_PRIMARY.name()};
        border-radius: 3px;
        background-color: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {MATERIAL_PRIMARY.name()};
        image: url(resources/check.png);
    }}
    QCheckBox::indicator:hover {{
        border: 1px solid {MATERIAL_PRIMARY.lighter(110).name()};
    }}
"""
)

OTDL_CELL_LABEL_STYLE = (
    lambda row_color: f"""
    color: {calculate_optimal_gray(row_color).name()};
    font-size: 11px;
"""
)

# Violation Header Styles
VIOLATION_HEADER_LABEL_STYLE = f"""
    QLabel {{
        color: {MATERIAL_PRIMARY.name()};
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 12px;
        font-weight: bold;
        padding: 3px 6px;
        background-color: {MATERIAL_SURFACE.name()};
        border-radius: 3px;
    }}
"""

VIOLATION_HEADER_WIDGET_STYLE = f"""
    QWidget {{
        background-color: {MATERIAL_BACKGROUND.name()};
        margin: 0px;
        padding: 5px;
    }}
"""

# Update About Dialog Style to use common button style
ABOUT_DIALOG_STYLE = f"""
    QDialog {{
        background-color: {MATERIAL_SURFACE.name()};
        min-width: 400px;
        min-height: 200px;
    }}
    QLabel {{
        color: {COLOR_TEXT_LIGHT.name()};
        font-size: 12px;
        padding: 8px;
        line-height: 1.4;
    }}
    QLabel#titleLabel {{
        font-size: 14px;
        font-weight: bold;
        color: {QColor(*RGB_IRIS).name()};
    }}
    QLabel#iconLabel {{
        padding: 16px;
        background-color: transparent;
    }}
    {BUTTON_STYLE}
"""

# Common scrollbar style using Rosé Pine colors
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background-color: {MATERIAL_BACKGROUND.name()};
        width: 14px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {HIGHLIGHT_MED};
        min-height: 30px;
        border-radius: 7px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {HIGHLIGHT_HIGH};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
        border: none;
        background: none;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background-color: {MATERIAL_BACKGROUND.name()};
        height: 14px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {HIGHLIGHT_MED};
        min-width: 30px;
        border-radius: 7px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {HIGHLIGHT_HIGH};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
        border: none;
        background: none;
    }}
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""


def apply_material_dark_theme(app: QApplication):
    """Apply Material Dark theme to the entire application."""
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

    # Global stylesheet for material look - now including scrollbars
    app.setStyleSheet(
        f"""
        QMainWindow, QDialog {{
            background-color: {MATERIAL_BACKGROUND.name()};
        }}
        QWidget {{
            font-family: Roboto, Arial, sans-serif;
        }}
        {BUTTON_STYLE}
        QLineEdit {{
            background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.3)};
            color: {COLOR_TEXT_LIGHT.name()};
            border: 1px solid {rgba(RGB_HIGHLIGHT_MED, 0.4)};
            padding: 6px;
            border-radius: 4px;
            selection-background-color: {rgba(RGB_IRIS, ALPHA_SELECTED)};
            selection-color: {COLOR_TEXT_LIGHT.name()};
        }}
        QLineEdit:focus {{
            border: 1px solid {QColor(*RGB_IRIS).name()};
            background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.4)};
        }}
        QLineEdit:hover {{
            background-color: {rgba(RGB_HIGHLIGHT_LOW, 0.35)};
            border: 1px solid {rgba(RGB_HIGHLIGHT_MED, 0.5)};
        }}
        QLineEdit::placeholder {{
            color: {rgba(RGB_TEXT, 0.4)};
        }}
        {SCROLLBAR_STYLE}
        """
    )
