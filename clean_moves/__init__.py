"""Clean moves package for handling invalid moves data.

This package provides functionality for:
1. Detecting moves with invalid route numbers
2. Cleaning and formatting moves data
3. Managing the UI for moves cleaning
"""

from clean_moves.clean_moves_manager import MovesManager
from clean_moves.ui.clean_moves_dialog import (
    CleanMovesDialog,
    EditMovesDialog,
    SplitMoveDialog,
)
from clean_moves.utils.clean_moves_utils import (
    detect_invalid_moves,
    format_moves_breakdown,
    get_valid_routes,
    parse_moves_entry,
    update_moves_in_database,
    validate_move_times,
    validate_route_number,
)

__all__ = [
    "CleanMovesDialog",
    "EditMovesDialog",
    "SplitMoveDialog",
    "MovesManager",
    "detect_invalid_moves",
    "format_moves_breakdown",
    "get_valid_routes",
    "parse_moves_entry",
    "update_moves_in_database",
    "validate_move_times",
    "validate_route_number",
]
