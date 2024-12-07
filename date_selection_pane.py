from PyQt5.QtCore import QDate, QEvent, Qt
from PyQt5.QtGui import QColor, QTextCharFormat
from PyQt5.QtWidgets import QCalendarWidget, QLabel, QPushButton, QVBoxLayout, QWidget

from custom_widgets import CustomTitleBarWidget


class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create white text format for current month days
        self.white_format = QTextCharFormat()
        self.white_format.setForeground(Qt.white)

        # Create dimmed format for other month days
        self.dimmed_format = QTextCharFormat()
        self.dimmed_format.setForeground(QColor("#323232"))

        # Apply the white format to weekday headers and weekend days
        self.setWeekdayTextFormat(Qt.Saturday, self.white_format)
        self.setWeekdayTextFormat(Qt.Sunday, self.white_format)

        # Set up the calendar's appearance with navigation bar styling
        self.setStyleSheet(
            """
            QCalendarWidget QAbstractItemView:!enabled {
                color: #323232;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #d8b4fc;  /* Light purple */
            }
            QCalendarWidget QToolButton {
                color: #000000;  /* Black text */
                background-color: transparent;
                border: none;
                border-radius: 0px;
                qproperty-iconSize: 24px;
                padding: 4px;
            }
            /* Hover state for navigation buttons */
            QCalendarWidget QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            /* Previous/Next month buttons */
            QCalendarWidget QToolButton::menu-indicator,
            QCalendarWidget QToolButton::menu-arrow {
                image: none;  /* Remove default arrows */
            }
            /* Month/Year text button */
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                color: #000000;
                background-color: transparent;
                padding: 2px 8px;
            }
            QCalendarWidget QSpinBox {
                color: #000000;  /* Black text for year spinbox if visible */
            }
            /* Navigation Bar */
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                background-color: rgba(0, 0, 0, 0.2);  /* Darker background */
                border: 1px solid rgba(255, 255, 255, 0.2);  /* More visible border */
                border-radius: 4px;
                margin: 3px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 18px;
                color: #000000;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                qproperty-icon: none;
                qproperty-text: "◀";
            }
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                qproperty-icon: none;
                qproperty-text: "▶";
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
            QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {
                background-color: rgba(0, 0, 0, 0.3);  /* Darker hover */
                border: 1px solid rgba(255, 255, 255, 0.3);  /* Hover border */
            }
            """
        )

        # Connect to the currentPageChanged signal
        self.currentPageChanged.connect(self.update_date_formats)

        # Initial update
        self.update_date_formats()

    def update_date_formats(self):
        """Update the text formats when the month changes"""
        # Get the current month's dates
        current = self.selectedDate()
        first_day = QDate(current.year(), current.month(), 1)
        last_day = first_day.addMonths(1).addDays(-1)

        # Reset all dates to dimmed format
        self.setDateTextFormat(QDate(), self.dimmed_format)

        # Set current month dates to white
        for d in range(first_day.daysTo(last_day) + 1):
            current_date = first_day.addDays(d)
            self.setDateTextFormat(current_date, self.white_format)


class DateSelectionPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.parent_main = parent

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBarWidget(title="Date Selection", parent=self)
        if hasattr(self.title_bar, "minimize_btn"):
            self.title_bar.minimize_btn.clicked.disconnect()
            self.title_bar.minimize_btn.clicked.connect(self.minimize_to_button)
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        self.calendar = CustomCalendarWidget()
        self.calendar.setFirstDayOfWeek(Qt.Saturday)
        self.calendar.setMinimumSize(280, 280)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

        content_layout.addWidget(self.calendar)

        apply_button = QPushButton("Apply Date Range")
        apply_button.setFixedWidth(200)
        apply_button.clicked.connect(self.apply_date_range_wrapper)
        content_layout.addWidget(apply_button, alignment=Qt.AlignCenter)

        instruction_label = QLabel("Select a Saturday, and press 'Apply Date Range'.")
        instruction_label.setWordWrap(True)
        instruction_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(instruction_label)

        main_layout.addWidget(content_widget)

    def minimize_to_button(self):
        if self.parent_main and hasattr(self.parent_main, "date_selection_button"):
            self.parent_main.date_selection_button.setChecked(False)
        self.hide()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                self.minimize_to_button()
                event.accept()
        super().changeEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.parent_main and hasattr(self.parent_main, "date_selection_button"):
            self.parent_main.date_selection_button.setChecked(False)

    def apply_date_range_wrapper(self):
        if self.parent_main and hasattr(self.parent_main, "apply_date_range"):
            self.parent_main.apply_date_range()

    def showEvent(self, event):
        """Override showEvent to set the fixed size after the window is shown"""
        super().showEvent(event)
        # Wait for the window to be shown and all widgets to be properly laid out
        self.setFixedSize(self.sizeHint())
