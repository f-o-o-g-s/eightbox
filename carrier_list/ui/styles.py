"""Material Design styles for carrier list UI components."""

from theme import (
    ALPHA_HOVER,
    ALPHA_PRESSED,
    BUTTON_STYLE,
    COLOR_BLACK,
    COLOR_ROW_HIGHLIGHT,
    COLOR_STATUS_NL,
    COLOR_STATUS_PTF,
    COLOR_TEXT_DIM,
    COLOR_TEXT_LIGHT,
    MATERIAL_BACKGROUND,
    MATERIAL_PRIMARY,
    MATERIAL_SECONDARY,
    MATERIAL_SURFACE,
)

STATS_PANEL_STYLE = f"""
QWidget {{
    background-color: {MATERIAL_SURFACE.name()};
    border: 1px solid {COLOR_TEXT_DIM.name()};
    border-radius: 4px;
    padding: 8px;
    margin-bottom: 10px;
}}
QLabel {{
    color: {COLOR_TEXT_LIGHT.name()};
    font-size: 13px;
    padding: 4px;
}}
QLabel[class="stat-value"][status="all"] {{
    color: {COLOR_TEXT_LIGHT.name()};
    font-weight: 500;
}}
QLabel[class="stat-value"][status="otdl"] {{
    color: {MATERIAL_PRIMARY.name()};  /* Purple */
    font-weight: 500;
}}
QLabel[class="stat-value"][status="wal"] {{
    color: {MATERIAL_SECONDARY.name()};  /* Teal */
    font-weight: 500;
}}
QLabel[class="stat-value"][status="nl"] {{
    color: {COLOR_STATUS_NL.name()};  /* Light Green */
    font-weight: 500;
}}
QLabel[class="stat-value"][status="ptf"] {{
    color: {COLOR_STATUS_PTF.name()};  /* Pink */
    font-weight: 500;
}}
QWidget[class="stat-container"] {{
    border-radius: 4px;
    padding: 4px 12px;
}}
QWidget[class="stat-container"]:hover {{
    background-color: rgba(187, 134, 252, {ALPHA_HOVER});
}}
QWidget[class="stat-container"][selected="true"] {{
    background-color: rgba(187, 134, 252, {ALPHA_PRESSED});
}}
"""

SEARCH_BAR_STYLE = f"""
QLineEdit {{
    background-color: {COLOR_ROW_HIGHLIGHT.name()};
    color: {COLOR_TEXT_LIGHT.name()};
    border: 1px solid {COLOR_TEXT_DIM.name()};
    border-radius: 4px;
    padding: 8px 12px 8px 36px;  /* Added left padding for icon */
    font-size: 13px;
    selection-background-color: {MATERIAL_PRIMARY.name()};
    selection-color: black;
}}
QLineEdit:focus {{
    border: 1px solid {MATERIAL_PRIMARY.name()};
    background-color: {COLOR_ROW_HIGHLIGHT.name()};
}}
QLineEdit:hover {{
    background-color: {COLOR_ROW_HIGHLIGHT.lighter(110).name()};
}}
"""

SEARCH_ICON_STYLE = f"""
QLabel {{
    color: {COLOR_TEXT_DIM.name()};
    font-size: 16px;
    padding: 0px;
    margin: 0px;
}}
"""

TABLE_VIEW_STYLE = f"""
QTableView {{
    background-color: {MATERIAL_SURFACE.name()};
    alternate-background-color: transparent;
    gridline-color: transparent;
    border: 1px solid {COLOR_TEXT_DIM.name()};
    border-radius: 4px;
    selection-background-color: {MATERIAL_PRIMARY.name()};
    selection-color: {COLOR_BLACK.name()};
}}
QHeaderView::section {{
    background-color: {COLOR_ROW_HIGHLIGHT.name()};
    color: {COLOR_TEXT_LIGHT.name()};
    padding: 8px;
    border: none;
    border-right: 1px solid {COLOR_TEXT_DIM.name()};
    border-bottom: 1px solid {COLOR_TEXT_DIM.name()};
}}
QTableView::item {{
    padding: 8px 4px;
    border-bottom: 1px solid {COLOR_TEXT_DIM.name()};
}}
QTableView::item:selected {{
    background: {MATERIAL_PRIMARY.name()};
    color: {COLOR_BLACK.name()};
}}
QTableView::item:hover {{
    background-color: rgba(187, 134, 252, {ALPHA_HOVER});
}}
QTableView::item:focus {{
    background: {MATERIAL_PRIMARY.name()};
    color: {COLOR_BLACK.name()};
    outline: none;
}}
QTableView::item:selected:focus {{
    background: {MATERIAL_PRIMARY.name()};
    color: {COLOR_BLACK.name()};
    outline: none;
}}
"""

BUTTON_CONTAINER_STYLE = f"""
QWidget {{
    background-color: {MATERIAL_BACKGROUND.darker(110).name()};
    border: 1px solid {COLOR_TEXT_DIM.name()};
    border-radius: 4px;
    margin-top: 8px;
}}
{BUTTON_STYLE}
QPushButton {{
    min-height: 28px;
    min-width: 60px;
    font-size: 11px;
    text-transform: uppercase;
    padding: 4px 8px;
}}
"""

EDIT_DIALOG_STYLE = f"""
QWidget {{
    background-color: {MATERIAL_BACKGROUND.name()};
    color: {COLOR_TEXT_LIGHT.name()};
}}
QLabel {{
    color: {COLOR_TEXT_LIGHT.name()};
    font-size: 13px;
    font-weight: bold;
    padding: 4px;
    margin-top: 8px;
}}
QLineEdit {{
    background-color: {MATERIAL_SURFACE.name()};
    color: {COLOR_TEXT_LIGHT.name()};
    border: 2px solid {COLOR_TEXT_DIM.name()};
    border-radius: 4px;
    padding: 12px;
    margin: 4px 0px 12px 0px;
    font-size: 14px;
}}
QLineEdit:disabled {{
    background-color: {MATERIAL_BACKGROUND.name()};
    color: {COLOR_TEXT_DIM.name()};
    border: 1px solid {COLOR_TEXT_DIM.name()};
}}
QComboBox {{
    background-color: {MATERIAL_SURFACE.name()};
    color: {COLOR_TEXT_LIGHT.name()};
    border: 2px solid {COLOR_TEXT_DIM.name()};
    border-radius: 4px;
    padding: 12px;
    padding-right: 36px;
    margin: 4px 0px 12px 0px;
    font-size: 14px;
    min-width: 200px;
}}
QComboBox::drop-down {{
    border: none;
    width: 36px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {MATERIAL_PRIMARY.name()};
    width: 10px;
    height: 10px;
    margin-right: 12px;
}}
QComboBox:hover {{
    border-color: {MATERIAL_PRIMARY.name()};
}}
QComboBox:focus {{
    border: 2px solid {MATERIAL_PRIMARY.name()};
}}
QComboBox QAbstractItemView {{
    background-color: {MATERIAL_SURFACE.name()};
    color: {COLOR_TEXT_LIGHT.name()};
    selection-background-color: {MATERIAL_PRIMARY.name()};
    selection-color: black;
    border: 1px solid {COLOR_TEXT_DIM.name()};
    padding: 4px;
}}
{BUTTON_STYLE}
QPushButton {{
    padding: 12px 24px;
    min-width: 120px;
    font-size: 14px;
    text-transform: uppercase;
    margin: 8px;
}}
"""
