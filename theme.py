# theme.py
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QStyleFactory,
)

"""Theme configuration and styling for the application.

This module contains color schemes, style definitions, and other UI theming
constants used throughout the application to maintain a consistent look and feel.
"""

# Material Design Dark Theme Colors
MATERIAL_PRIMARY = QColor("#BB86FC")  # Purple-ish
MATERIAL_PRIMARY_VARIANT = QColor("#3700B3")
MATERIAL_SECONDARY = QColor("#03DAC6")  # Teal
MATERIAL_BACKGROUND = QColor("#121212")  # Dark background
MATERIAL_SURFACE = QColor("#1E1E1E")  # Slightly lighter surface
MATERIAL_ERROR = QColor("#CF6679")  # Error red

# Existing color mappings updated to material theme
COLOR_ROW_HIGHLIGHT = QColor("#2D2D2D")  # Slightly lighter than surface
COLOR_CELL_HIGHLIGHT = MATERIAL_PRIMARY.darker(150)
COLOR_WEEKLY_REMEDY = MATERIAL_SECONDARY.darker(150)
COLOR_NO_HIGHLIGHT = MATERIAL_SURFACE
COLOR_TEXT_LIGHT = QColor("#E1E1E1")  # Near-white text
COLOR_TEXT_DIM = QColor(
    "#333333"
)  # Much darker gray (almost black) for light backgrounds
COLOR_MAXIMIZED_TRUE = QColor("#4CAF50")  # Material green
COLOR_MAXIMIZED_FALSE = QColor("#F44336")  # Material red


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
        }
        QHeaderView::section {
            background-color: #2D2D2D;
            color: #E1E1E1;
            padding: 4px;
            border: 1px solid #333333;
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
