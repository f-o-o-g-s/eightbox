from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QMenu, QTableView


def setup_table_copy_functionality(table_view):
    """
    Adds right-click and Ctrl+C copy functionality to a QTableView or QTableWidget.

    Args:
        table_view (QTableView or QTableWidget): The table view to enhance.
    """
    # Enable custom context menu
    table_view.setContextMenuPolicy(Qt.CustomContextMenu)
    table_view.customContextMenuRequested.connect(
        lambda position: show_context_menu(table_view, position)
    )

    # Enable selection
    table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table_view.setSelectionBehavior(QAbstractItemView.SelectItems)

    # Override the keyPressEvent for Ctrl+C support
    original_key_press_event = table_view.keyPressEvent

    def keyPressEvent(event):
        if (
            event.key() == Qt.Key_C
            and QApplication.keyboardModifiers() == Qt.ControlModifier
        ):
            print("Ctrl+C detected. Initiating copy...")
            copy_selection(table_view)
        else:
            original_key_press_event(event)

    table_view.keyPressEvent = keyPressEvent


def show_context_menu(table_view, position):
    """Display the context menu for copying selected items."""
    print("Displaying context menu...")
    selection_model = table_view.selectionModel()
    if not selection_model.hasSelection():
        print("No selection found for context menu.")
        return  # No selection to copy

    menu = QMenu()
    copy_action = menu.addAction("Copy")
    action = menu.exec_(table_view.viewport().mapToGlobal(position))

    if action == copy_action:
        print("Copy action selected from context menu.")
        copy_selection(table_view)


def copy_selection(table_view):
    """Copy the selected items and column headers from the QTableView to the clipboard."""
    print("Copy selection initiated.")
    selection_model = table_view.selectionModel()
    if not selection_model.hasSelection():
        print("No selection found.")
        return

    # Get the model
    model = table_view.model()
    selected_indices = selection_model.selectedIndexes()

    # Determine selected columns and rows
    selected_columns = sorted(set(index.column() for index in selected_indices))
    selected_rows = sorted(set(index.row() for index in selected_indices))

    # Fetch headers
    headers = [
        model.headerData(col, Qt.Horizontal, Qt.DisplayRole) for col in selected_columns
    ]
    print(f"Headers: {headers}")

    # Fetch rows
    rows = []
    for row in selected_rows:
        row_data = []
        for col in selected_columns:
            index = model.index(row, col)
            cell_data = model.data(index, Qt.DisplayRole)
            row_data.append(cell_data if cell_data is not None else "")
            print(f"Row {row}, Col {col}, Value: {cell_data}")
        rows.append("\t".join(row_data))

    # Combine headers and rows into a single string
    clipboard_text = "\t".join(headers) + "\n" + "\n".join(rows)
    print("Generated clipboard text:")
    print(clipboard_text)

    # Copy the text to the clipboard
    clipboard = QApplication.clipboard()
    clipboard.setText(clipboard_text)
    print("Copy to clipboard completed.")


def extract_table_state(table_view):
    """Extract content, formatting metadata, and row highlights from a QTableView."""
    if not isinstance(table_view, QTableView):
        return None, None, None

    model = table_view.model()

    # Support both proxy and source models
    if isinstance(model, QSortFilterProxyModel):
        source_model = model.sourceModel()
    else:
        source_model = model

    # Get only visible columns
    visible_columns = []
    for col in range(source_model.columnCount()):
        if not table_view.isColumnHidden(col):
            visible_columns.append(col)

    # Use the model's built-in state extraction for visible columns
    content_df, metadata_df, row_highlights_df = source_model.get_table_state()

    # Filter for visible columns
    visible_headers = [
        source_model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
        for col in visible_columns
    ]
    content_df = content_df[visible_headers]
    metadata_df = metadata_df[visible_headers]

    return content_df, metadata_df, row_highlights_df
