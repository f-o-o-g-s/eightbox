"""Dialog for cleaning invalid moves data.

This module provides a dialog interface for:
1. Viewing moves entries with invalid route numbers
2. Editing route numbers with validation
3. Applying changes to the moves data
"""

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clean_moves_utils import (
    format_moves_breakdown,
    parse_moves_entry,
    update_moves_in_database,
    validate_route_number,
    validate_time_input,
)
from custom_widgets import (
    CustomTitleBarWidget,
    CustomWarningDialog,
)


class SplitMoveDialog(QDialog):
    """Dialog for splitting a move into multiple parts with custom times and routes."""

    def __init__(self, start_time, end_time, route, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)

        # Store original values
        self.original_start = start_time
        self.original_end = end_time
        self.original_route = route

        # Initialize UI elements that are referenced in other methods
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.ok_button.setEnabled(False)

        self.add_move_button = QPushButton("Add Split")
        self.add_move_button.clicked.connect(self.add_split)
        self.add_move_button.setEnabled(True)  # Will be updated after adding first move

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("Split Move", self)
        layout.addWidget(self.title_bar)

        # Content widget with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Create scroll area for moves
        self.moves_layout = QVBoxLayout()
        self.move_groups = []

        # Add first move
        self.add_move_group(0, start_time, route)

        # Add buttons
        button_box = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(self.add_move_button)
        button_box.addStretch()
        button_box.addWidget(self.ok_button)
        button_box.addWidget(cancel_button)

        # Add layouts to content layout
        content_layout.addLayout(self.moves_layout)
        content_layout.addLayout(button_box)

        # Add content widget to main layout
        layout.addWidget(content_widget)

        # Set style
        self.setStyleSheet(
            """
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
        )

    def add_move_group(self, index, start_time=None, route=None):
        """Add a new move group to the dialog."""
        group = QGroupBox(f"Move {index + 1}")
        layout = QGridLayout()

        # Create inputs
        start_input = QLineEdit()
        if index == 0 and start_time is not None:  # First move gets original start time
            start_input.setText(f"{start_time:.2f}")
            start_input.setEnabled(False)  # Disable editing for first move's start time
            start_input.setStyleSheet(
                """
                QLineEdit:disabled {
                    background-color: #1E1E1E;
                    color: #808080;
                    border: 1px solid #404040;
                }
            """
            )
        start_input.setPlaceholderText("HH.MM")
        start_input.setMaxLength(5)

        end_input = QLineEdit()
        if index == 0:  # First move
            end_input.setPlaceholderText("HH.MM")
        end_input.setMaxLength(5)

        route_input = QLineEdit()
        if route:
            route_input.setText(route)
        route_input.setMaxLength(5)
        route_input.setPlaceholderText("Enter 4 or 5-digit route")

        # Add to layout
        layout.addWidget(QLabel("Start Time:"), 0, 0)
        layout.addWidget(start_input, 0, 1)
        layout.addWidget(QLabel("End Time:"), 1, 0)
        layout.addWidget(end_input, 1, 1)
        layout.addWidget(QLabel("Route:"), 2, 0)
        layout.addWidget(route_input, 2, 1)

        # Add remove button for all except first move
        if index > 0:
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda: self.remove_move_group(group))
            layout.addWidget(remove_button, 3, 0, 1, 2)

        group.setLayout(layout)

        # Store references to inputs
        group.start_input = start_input
        group.end_input = end_input
        group.route_input = route_input

        # Connect validation
        start_input.textChanged.connect(self.validate_inputs)
        end_input.textChanged.connect(self.validate_inputs)
        route_input.textChanged.connect(self.validate_inputs)

        # Add to moves layout
        self.moves_layout.addWidget(group)
        self.move_groups.append(group)

        # Update add button state
        self.add_move_button.setEnabled(len(self.move_groups) < 4)

        # Validate inputs
        self.validate_inputs()

    def add_split(self):
        """Add a new split to the moves."""
        if len(self.move_groups) < 4:
            self.add_move_group(len(self.move_groups))

    def remove_move_group(self, group):
        """Remove a move group from the dialog."""
        group.hide()
        self.moves_layout.removeWidget(group)
        self.move_groups.remove(group)
        group.deleteLater()

        # Renumber remaining groups
        for i, group in enumerate(self.move_groups):
            group.setTitle(f"Move {i + 1}")

        # Update add button state
        self.add_move_button.setEnabled(len(self.move_groups) < 4)

        # Validate inputs
        self.validate_inputs()

    def validate_inputs(self):
        """Validate all input fields."""
        try:
            valid = True
            prev_end = None

            for group in self.move_groups:
                # Get values
                start = float(group.start_input.text() or "0")
                end = float(group.end_input.text() or "0")
                route = group.route_input.text()

                # Validate times in centesimal format
                if not validate_time_input(
                    group.start_input.text()
                ) or not validate_time_input(group.end_input.text()):
                    valid = False
                    break

                # Validate route
                if not validate_route_number(route, set()):
                    valid = False
                    break

                # Validate connection to previous move
                if prev_end is not None and start != prev_end:
                    valid = False
                    break

                prev_end = end

            # Validate first and last times match original
            if valid and self.move_groups:
                first_start = float(self.move_groups[0].start_input.text() or "0")
                last_end = float(self.move_groups[-1].end_input.text() or "0")
                valid = (
                    first_start == self.original_start and last_end == self.original_end
                )

            self.ok_button.setEnabled(valid and len(self.move_groups) > 0)

        except ValueError:
            self.ok_button.setEnabled(False)

    def get_result(self):
        """Get all move values.

        Returns:
            List of [start1, end1, route1, start2, end2, route2, ...]
        """
        result = []
        for group in self.move_groups:
            result.extend(
                [
                    group.start_input.text(),
                    group.end_input.text(),
                    group.route_input.text().zfill(4),
                ]
            )
        return result

    def validate_and_accept(self):
        """Validate final values and accept dialog."""
        try:
            if not self.move_groups:
                self.reject()
                return

            # Get first and last times
            first_start = float(self.move_groups[0].start_input.text())
            last_end = float(self.move_groups[-1].end_input.text())

            # Validate that first and last times match original
            if first_start == self.original_start and last_end == self.original_end:
                self.accept()
            else:
                CustomWarningDialog.warning(
                    self,
                    "Invalid Times",
                    "Start and end times must match original move.",
                )
        except ValueError:
            self.reject()


class EditMovesDialog(QDialog):
    """Dialog for editing individual moves."""

    def __init__(self, moves_str, valid_routes, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.valid_routes = valid_routes

        # Parse moves
        self.moves = parse_moves_entry(moves_str)

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("Edit Moves", self)
        layout.addWidget(self.title_bar)

        # Content widget with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Create scroll area for moves
        self.moves_layout = QVBoxLayout()

        # Create buttons first
        button_box = QHBoxLayout()

        self.add_move_button = QPushButton("Add Move")
        self.add_move_button.clicked.connect(self.add_new_move)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(self.add_move_button)
        button_box.addStretch()
        button_box.addWidget(self.ok_button)
        button_box.addWidget(cancel_button)

        # Add each move as a group
        for i, (start, end, route) in enumerate(self.moves):
            self.add_move_group(start, end, route)

        # Add layouts to content layout
        content_layout.addLayout(self.moves_layout)
        content_layout.addLayout(button_box)

        # Add content widget to main layout
        layout.addWidget(content_widget)

        # Set style
        self.setStyleSheet(
            """
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
        )

        # Initial validation
        self.validate_inputs()

    def add_move_group(self, start=None, end=None, route=None):
        """Add a new move group to the dialog."""
        group = QGroupBox(f"Move {self.moves_layout.count() + 1}")
        group_layout = QGridLayout()

        # Create inputs
        start_input = QLineEdit()
        if start is not None:
            start_input.setText(f"{start:.2f}")
        start_input.setPlaceholderText("HH.MM")
        start_input.setMaxLength(5)

        end_input = QLineEdit()
        if end is not None:
            end_input.setText(f"{end:.2f}")
        end_input.setPlaceholderText("HH.MM")
        end_input.setMaxLength(5)

        route_input = QLineEdit()
        if route:
            route_input.setText(route)
        route_input.setMaxLength(5)
        route_input.setPlaceholderText("Enter 4 or 5-digit route")

        # Add to layout
        group_layout.addWidget(QLabel("Start Time:"), 0, 0)
        group_layout.addWidget(start_input, 0, 1)
        group_layout.addWidget(QLabel("End Time:"), 1, 0)
        group_layout.addWidget(end_input, 1, 1)
        group_layout.addWidget(QLabel("Route:"), 2, 0)
        group_layout.addWidget(route_input, 2, 1)

        # Add remove button if not the first move
        if self.moves_layout.count() > 0:
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda: self.remove_move_group(group))
            group_layout.addWidget(remove_button, 3, 0, 1, 2)

        group.setLayout(group_layout)

        # Store references to inputs
        group.start_input = start_input
        group.end_input = end_input
        group.route_input = route_input

        # Connect validation
        start_input.textChanged.connect(self.validate_inputs)
        end_input.textChanged.connect(self.validate_inputs)
        route_input.textChanged.connect(self.validate_inputs)

        self.moves_layout.addWidget(group)

        # Update add button state (limit to 4 moves)
        self.add_move_button.setEnabled(self.moves_layout.count() < 4)

    def add_new_move(self):
        """Add a new empty move group."""
        if self.moves_layout.count() < 4:
            self.add_move_group()
            self.validate_inputs()

    def remove_move_group(self, group):
        """Remove a move group from the dialog."""
        group.hide()
        self.moves_layout.removeWidget(group)
        group.deleteLater()

        # Renumber remaining groups
        for i in range(self.moves_layout.count()):
            group = self.moves_layout.itemAt(i).widget()
            if isinstance(group, QGroupBox):
                group.setTitle(f"Move {i + 1}")

        # Update add button state
        self.add_move_button.setEnabled(self.moves_layout.count() < 4)

        # Validate inputs
        self.validate_inputs()

    def validate_inputs(self):
        """Validate all input fields."""
        try:
            valid = True

            for i in range(self.moves_layout.count()):
                group = self.moves_layout.itemAt(i).widget()
                if not isinstance(group, QGroupBox):
                    continue

                # Get values
                start_text = group.start_input.text().strip()
                end_text = group.end_input.text().strip()
                route = group.route_input.text().strip()

                # Check if all fields have values
                if not start_text or not end_text or not route:
                    valid = False
                    break

                # Convert times to float for comparison
                start = float(start_text)
                end = float(end_text)

                # Validate times
                if not validate_time_input(start_text) or not validate_time_input(
                    end_text
                ):
                    valid = False
                    break

                # Validate end time is after start time
                if end <= start:
                    valid = False
                    break

                # Validate route
                if not validate_route_number(route, self.valid_routes):
                    valid = False
                    break

            self.ok_button.setEnabled(valid and self.moves_layout.count() > 0)

        except (ValueError, AttributeError):
            self.ok_button.setEnabled(False)

    def get_result(self):
        """Get all move values.

        Returns:
            List of [start1, end1, route1, start2, end2, route2, ...]
        """
        result = []
        for i in range(self.moves_layout.count()):
            group = self.moves_layout.itemAt(i).widget()
            if not isinstance(group, QGroupBox):
                continue
            result.extend(
                [
                    group.start_input.text(),
                    group.end_input.text(),
                    group.route_input.text().zfill(4),
                ]
            )
        return result

    def validate_and_accept(self):
        """Validate final values and accept dialog."""
        try:
            if not self.moves_layout.count():
                self.reject()
                return

            # Do one final validation
            valid = True
            prev_end = None

            for i in range(self.moves_layout.count()):
                group = self.moves_layout.itemAt(i).widget()
                if not isinstance(group, QGroupBox):
                    continue

                # Get values
                start = float(group.start_input.text() or "0")
                end = float(group.end_input.text() or "0")
                route = group.route_input.text()

                # Validate times
                if not validate_time_input(
                    group.start_input.text()
                ) or not validate_time_input(group.end_input.text()):
                    valid = False
                    break

                # Validate route
                if not validate_route_number(route, self.valid_routes):
                    valid = False
                    break

                # Validate connection to previous move
                if prev_end is not None and start != prev_end:
                    valid = False
                    break

                prev_end = end

            if valid:
                self.accept()
            else:
                CustomWarningDialog.warning(
                    self,
                    "Invalid Input",
                    "Please check that all times and routes are valid and moves are connected.",
                )
        except ValueError:
            self.reject()


class CleanMovesDialog(QDialog):
    """Dialog for cleaning invalid moves data.

    Provides a table view of moves entries with invalid route numbers
    and controls for editing them.

    Signals:
        moves_cleaned: Emitted when moves data is cleaned and saved
    """

    moves_cleaned = pyqtSignal(dict)  # Signal emitted when moves are cleaned

    def __init__(self, invalid_moves_df, valid_routes, parent=None):
        """Initialize the dialog.

        Args:
            invalid_moves_df: DataFrame containing moves entries with invalid routes
            valid_routes: Set of valid route numbers
            parent: Parent widget
        """
        super().__init__(parent)
        self.invalid_moves = invalid_moves_df
        self.valid_routes = valid_routes
        self.cleaned_moves = {}  # Store cleaned moves data
        self.current_row = None  # Currently selected row

        # Get database path from parent (MainApp)
        self.db_path = parent.mandates_db_path if parent else None
        if not self.db_path:
            raise ValueError("Database path not available")

        # Set window flags for frameless window
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Make dialog modal
        self.setWindowModality(Qt.ApplicationModal)

        # Set minimum and initial size
        self.setMinimumSize(1500, 800)  # Minimum size
        self.resize(1500, 800)  # Initial size

        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBarWidget("Clean Invalid Moves", self)
        layout.addWidget(self.title_bar)

        # Content widget with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Add table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Carrier Name",
                "Date",
                "Original Moves",
                "Moves Breakdown",
                "Fixed Moves",
                "Original Hours",
                "Fixed Hours",
                "Issue",
                "Status",
            ]
        )

        # Set selection behavior to select entire rows
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Set alternating row colors for better readability
        self.table.setAlternatingRowColors(True)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)

        # Populate table
        self.populate_table()
        content_layout.addWidget(self.table)

        # Add buttons
        button_row = QHBoxLayout()

        self.edit_button = QPushButton("Edit Moves")
        self.edit_button.clicked.connect(self.edit_moves)
        self.edit_button.setEnabled(False)

        self.restore_button = QPushButton("Restore Moves")
        self.restore_button.clicked.connect(self.restore_moves)
        self.restore_button.setEnabled(False)

        self.clear_button = QPushButton("Clear Moves")
        self.clear_button.clicked.connect(self.clear_moves)
        self.clear_button.setEnabled(False)

        button_row.addWidget(self.edit_button)
        button_row.addWidget(self.restore_button)
        button_row.addWidget(self.clear_button)

        content_layout.addLayout(button_row)

        # Add dialog buttons
        dialog_button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save All")
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet(
            """
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
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(
            """
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
        )

        dialog_button_layout.addWidget(self.save_button)
        dialog_button_layout.addWidget(self.cancel_button)
        content_layout.addLayout(dialog_button_layout)

        # Add content widget to main layout
        layout.addWidget(content_widget)

        # Set dialog style
        self.setStyleSheet(
            """
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
        )

        # Connect signals
        self.table.itemSelectionChanged.connect(self.handle_selection)

    def populate_table(self):
        """Populate the table with invalid moves data."""
        self.table.setRowCount(len(self.invalid_moves))

        for i, (_, row) in enumerate(self.invalid_moves.iterrows()):
            # Add carrier name
            name_item = QTableWidgetItem(row["carrier_name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)

            # Add date
            date_item = QTableWidgetItem(row["rings_date"])
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 1, date_item)

            # Add moves
            moves_item = QTableWidgetItem(row["moves"])
            moves_item.setFlags(moves_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 2, moves_item)

            # Add moves breakdown
            breakdown_item = QTableWidgetItem(row["Moves Breakdown"])
            breakdown_item.setFlags(breakdown_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 3, breakdown_item)

            # Add empty fixed moves
            fixed_item = QTableWidgetItem("")
            fixed_item.setFlags(fixed_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 4, fixed_item)

            # Add original total hours
            hours_item = QTableWidgetItem(f"{row['Total Moves Hours']:.2f}")
            hours_item.setFlags(hours_item.flags() & ~Qt.ItemIsEditable)
            if row["Total Moves Hours"] > 4.25:
                hours_item.setData(Qt.UserRole, "warning")
            self.table.setItem(i, 5, hours_item)

            # Add empty fixed hours
            fixed_hours_item = QTableWidgetItem("")
            fixed_hours_item.setFlags(fixed_hours_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 6, fixed_hours_item)

            # Add issue
            issue_item = QTableWidgetItem(row["Issue"])
            issue_item.setFlags(issue_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 7, issue_item)

            # Add status
            status_item = QTableWidgetItem("Not Fixed")
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_item.setBackground(QColor("#B71C1C"))  # Material Design dark red 900
            status_item.setForeground(
                QColor("#EF9A9A")
            )  # Material Design red 200 for better contrast
            self.table.setItem(i, 8, status_item)

    def calculate_total_hours(self, moves_str):
        """Calculate total hours from a moves string.

        Args:
            moves_str: String of moves in format "start1,end1,route1,start2,end2,route2,..."

        Returns:
            float: Total hours from all moves
        """
        if not moves_str:
            return 0.0

        try:
            moves = parse_moves_entry(moves_str)
            total_hours = 0.0
            for start, end, _ in moves:
                hours = end - start
                if hours < 0:  # Handle moves crossing midnight
                    hours += 24
                total_hours += hours
            return total_hours
        except Exception:
            return 0.0

    def handle_selection(self):
        """Handle table row selection."""
        selected = self.table.selectedItems()
        if selected:
            self.current_row = selected[0].row()

            # Get the issue for this row
            moves = self.table.item(self.current_row, 2).text()

            # Enable buttons
            self.clear_button.setEnabled(True)
            self.restore_button.setEnabled(True)

            # Parse moves to check if merge/split/edit is possible
            move_list = parse_moves_entry(moves)
            self.edit_button.setEnabled(
                bool(move_list)
            )  # Enable edit if there are any moves

        else:
            self.current_row = None
            self.edit_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.restore_button.setEnabled(False)

    def clear_moves(self):
        """Clear all moves for the selected entry."""
        if self.current_row is None:
            return

        # Show confirmation dialog using CustomWarningDialog
        if (
            CustomWarningDialog.warning(
                self,
                "Confirm Clear",
                "This will remove all moves for this entry. Continue?",
                buttons=["Yes", "No"],
                default_button="No",
            )
            == "Yes"
        ):
            # Get current row data
            carrier = self.table.item(self.current_row, 0).text()
            date = self.table.item(self.current_row, 1).text()

            # Store empty string as the cleaned move (this is what gets saved to database)
            key = (carrier, date)
            self.cleaned_moves[key] = ""

            # Update fixed moves column with visual indicator
            fixed_item = self.table.item(self.current_row, 4)
            fixed_item.setText("(Moves Cleared)")
            fixed_item.setData(Qt.UserRole, "true")
            fixed_item.setBackground(Qt.transparent)

            # Update fixed hours
            fixed_hours_item = self.table.item(self.current_row, 6)
            fixed_hours_item.setText("0.00")
            fixed_hours_item.setData(Qt.UserRole, None)

            # Update status
            status_item = self.table.item(self.current_row, 8)
            status_item.setText("Fixed")
            status_item.setData(Qt.UserRole, "true")
            status_item.setBackground(QColor("#1B5E20"))  # Material Design green 900
            status_item.setForeground(QColor("#81C784"))  # Material Design green 300

            # Enable save button
            self.save_button.setEnabled(bool(self.cleaned_moves))

    def save_changes(self):
        """Save all cleaned moves to the database and close the dialog."""
        if not self.cleaned_moves:
            CustomWarningDialog.warning(
                self, "No Changes", "No moves have been cleaned yet."
            )
            return

        # Show confirmation dialog
        if (
            CustomWarningDialog.warning(
                self,
                "Confirm Save",
                "This will update the moves data in the database. Continue?",
                buttons=["Yes", "No"],
                default_button="No",
            )
            == "Yes"
        ):
            try:
                # Hide this dialog while processing
                self.hide()

                # Update database
                if not update_moves_in_database(self.db_path, self.cleaned_moves):
                    raise Exception("Failed to update moves in database")

                # Emit signal with cleaned moves for UI update
                self.moves_cleaned.emit(self.cleaned_moves)

                # Accept dialog (MainApp will handle progress and success message)
                self.accept()

            except Exception as e:
                CustomWarningDialog.warning(
                    self.parent(), "Error", f"Failed to update moves: {str(e)}"
                )

                # Show the dialog again since we had an error
                self.show()

    def restore_moves(self):
        """Restore moves to their original state."""
        if self.current_row is None:
            return

        # Show confirmation dialog
        if (
            CustomWarningDialog.warning(
                self,
                "Confirm Restore",
                "This will restore the original moves. Continue?",
                buttons=["Yes", "No"],
                default_button="No",
            )
            == "Yes"
        ):
            # Get current row data
            carrier = self.table.item(self.current_row, 0).text()
            date = self.table.item(self.current_row, 1).text()

            # Remove this entry from cleaned_moves if it exists
            key = (carrier, date)
            if key in self.cleaned_moves:
                del self.cleaned_moves[key]

            # Clear fixed moves column
            fixed_item = self.table.item(self.current_row, 4)
            fixed_item.setText("")
            fixed_item.setData(Qt.UserRole, None)
            fixed_item.setBackground(Qt.transparent)

            # Clear fixed hours
            fixed_hours_item = self.table.item(self.current_row, 6)
            fixed_hours_item.setText("")
            fixed_hours_item.setData(Qt.UserRole, None)

            # Reset status to Not Fixed
            status_item = self.table.item(self.current_row, 8)
            status_item.setText("Not Fixed")
            status_item.setData(Qt.UserRole, None)
            status_item.setBackground(Qt.transparent)

            # Enable save button if there are still other cleaned moves
            self.save_button.setEnabled(bool(self.cleaned_moves))

    def edit_moves(self):
        """Show dialog to edit individual moves."""
        if self.current_row is None:
            return

        # Get current row data
        moves = self.table.item(self.current_row, 2).text()

        # Show edit dialog
        dialog = EditMovesDialog(moves, self.valid_routes, self)
        if dialog.exec_() == QDialog.Accepted:
            # Get the edited moves
            new_moves = dialog.get_result()

            # Get current row data for database update
            carrier = self.table.item(self.current_row, 0).text()
            date = self.table.item(self.current_row, 1).text()

            # Create new moves string
            new_moves_str = ",".join(new_moves)

            # Store the cleaned move
            key = (carrier, date)
            self.cleaned_moves[key] = new_moves_str

            # Update fixed moves column
            fixed_breakdown = format_moves_breakdown(new_moves_str)
            fixed_item = self.table.item(self.current_row, 4)
            fixed_item.setText(fixed_breakdown)
            fixed_item.setData(Qt.UserRole, "true")
            fixed_item.setBackground(Qt.transparent)

            # Calculate and update fixed hours
            total_hours = self.calculate_total_hours(new_moves_str)
            fixed_hours_item = self.table.item(self.current_row, 6)
            fixed_hours_item.setText(f"{total_hours:.2f}")
            if total_hours > 4.25:
                fixed_hours_item.setData(Qt.UserRole, "warning")
            else:
                fixed_hours_item.setData(Qt.UserRole, None)

            # Update status
            status_item = self.table.item(self.current_row, 8)
            status_item.setText("Fixed")
            status_item.setData(Qt.UserRole, "true")
            status_item.setBackground(QColor("#1B5E20"))  # Material Design green 900
            status_item.setForeground(QColor("#81C784"))  # Material Design green 300

            # Enable save button
            self.save_button.setEnabled(bool(self.cleaned_moves))
