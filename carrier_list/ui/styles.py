"""Material Design styles for carrier list UI components."""

from theme import (
    COLOR_TEXT_DIM,
    COLOR_TEXT_LIGHT,
    MATERIAL_BACKGROUND,
    MATERIAL_PRIMARY,
    MATERIAL_SURFACE,
)

STATS_PANEL_STYLE = """
QWidget {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 8px;
    margin-bottom: 10px;
}
QLabel {
    color: #E1E1E1;
    font-size: 13px;
    padding: 4px;
}
QLabel[class="stat-value"][status="all"] {
    color: #E1E1E1;
    font-weight: 500;
}
QLabel[class="stat-value"][status="otdl"] {
    color: #BB86FC;  /* Purple */
    font-weight: 500;
}
QLabel[class="stat-value"][status="wal"] {
    color: #03DAC6;  /* Teal */
    font-weight: 500;
}
QLabel[class="stat-value"][status="nl"] {
    color: #64DD17;  /* Light Green */
    font-weight: 500;
}
QLabel[class="stat-value"][status="ptf"] {
    color: #FF7597;  /* Pink */
    font-weight: 500;
}
QWidget[class="stat-container"] {
    border-radius: 4px;
    padding: 4px 12px;
}
QWidget[class="stat-container"]:hover {
    background-color: rgba(103, 80, 164, 0.08);
}
QWidget[class="stat-container"][selected="true"] {
    background-color: rgba(103, 80, 164, 0.15);
}
"""

SEARCH_BAR_STYLE = """
QLineEdit {
    background-color: #262626;
    color: #E1E1E1;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 8px 12px 8px 36px;  /* Added left padding for icon */
    font-size: 13px;
    selection-background-color: #BB86FC;
    selection-color: #000000;
}
QLineEdit:focus {
    border: 1px solid #BB86FC;
    background-color: #2D2D2D;
}
QLineEdit:hover {
    background-color: #2A2A2A;
}
"""

SEARCH_ICON_STYLE = """
QLabel {
    color: #666666;
    font-size: 16px;
    padding: 0px;
    margin: 0px;
}
"""

TABLE_VIEW_STYLE = """
QTableView {
    background-color: #1E1E1E;
    alternate-background-color: transparent;
    gridline-color: transparent;
    border: 1px solid #333333;
    border-radius: 4px;
    selection-background-color: #BB86FC;
    selection-color: #000000;
}
QHeaderView::section {
    background-color: #2D2D2D;
    color: #E1E1E1;
    padding: 8px;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 1px solid #333333;
}
QTableView::item {
    padding: 8px 4px;
    border-bottom: 1px solid rgba(51, 51, 51, 0.5);
}
QTableView::item:selected {
    background: #BB86FC;
    color: #000000;
}
QTableView::item:hover {
    background-color: rgba(187, 134, 252, 0.1);
}
QTableView::item:focus {
    background: #BB86FC;
    color: #000000;
    outline: none;
}
QTableView::item:selected:focus {
    background: #BB86FC;
    color: #000000;
    outline: none;
}
"""

BUTTON_CONTAINER_STYLE = """
QWidget {
    background-color: #1A1A1A;
    border: 1px solid #333333;
    border-radius: 4px;
    margin-top: 8px;
}
QPushButton {
    background-color: #2D2D2D;
    color: #BB86FC;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 500;
    min-height: 28px;
    min-width: 60px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    background-color: #353535;
}
QPushButton:pressed {
    background-color: #252525;
}
QPushButton:disabled {
    background-color: #252525;
    color: rgba(225, 225, 225, 0.3);
}
QPushButton#primary {
    background-color: #BB86FC;
    color: #000000;
}
QPushButton#primary:hover {
    background-color: #CBB0FF;
}
QPushButton#primary:pressed {
    background-color: #9965DA;
}
QPushButton#destructive {
    background-color: #CF6679;
    color: #000000;
}
QPushButton#destructive:hover {
    background-color: #FF8296;
}
QPushButton#destructive:pressed {
    background-color: #B4424F;
}
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
QPushButton {{
    background-color: {MATERIAL_SURFACE.name()};
    color: {MATERIAL_PRIMARY.name()};
    border: 2px solid {MATERIAL_PRIMARY.name()};
    border-radius: 4px;
    padding: 12px 24px;
    font-weight: bold;
    min-width: 120px;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 8px;
}}
QPushButton:hover {{
    background-color: rgba(187, 134, 252, 0.1);
}}
QPushButton:pressed {{
    background-color: rgba(187, 134, 252, 0.2);
}}
QPushButton#primary {{
    background-color: {MATERIAL_PRIMARY.name()};
    color: black;
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {MATERIAL_PRIMARY.lighter(110).name()};
}}
QPushButton#primary:pressed {{
    background-color: {MATERIAL_PRIMARY.darker(110).name()};
}}
"""
