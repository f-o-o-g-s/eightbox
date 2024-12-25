"""Utility functions used throughout the application.

This module provides helper functions for data processing and display formatting.
Functions here are designed to be reusable across different parts of the application
and handle common tasks like formatting display indicators for various carrier statuses.
"""

import json
import os
import sys

import pandas as pd


def set_display(row):
    """Format display indicators for carrier status and leave types.

    Creates standardized display indicators based on carrier status codes and leave types.
    These indicators are used throughout the application to show carrier availability
    and schedule status.

    Args:
        row (pd.Series): A row from a DataFrame containing carrier status information.
            Expected to have 'code' and 'leave_type' columns, but will handle missing columns.

    Returns:
        str: A formatted display indicator in parentheses, or empty string if no special status.
            Possible values include:
            - "(NS protect)" for non-scheduled protection
            - "(annual)" for annual leave
            - "(guaranteed)" for guaranteed time
            - "(holiday)" for holiday leave
            - "(NS day)" for non-scheduled day
            - "(sick)" for sick leave
            - "(no call)" for no call status
            - "" (empty string) for no special status

    Note:
        All inputs are converted to lowercase and stripped for consistent comparison.
        The function uses .get() to safely handle missing columns in the input row.
    """
    code = (
        str(row.get("code", "")).strip().lower()
    )  # Use .get to avoid KeyError if column is missing
    leave_type = str(row.get("leave_type", "")).strip().lower()

    # Check for specific leave indicators
    if code == "annual" and leave_type == "none":
        return "(NS protect)"
    if code == "annual" and leave_type == "annual":
        return "(annual)"
    if code == "none" and leave_type == "annual":
        return "(annual)"
    if code == "none" and leave_type == "guaranteed":
        return "(guaranteed)"
    if code == "none" and leave_type == "holiday":
        return "(holiday)"
    if code == "ns day" and leave_type == "none":
        return "(NS day)"
    if code == "sick" and leave_type == "sick":
        return "(sick)"
    if code == "none" and leave_type == "sick":
        return "(sick)"
    if code == "no call" and leave_type == "none":
        return "(no call)"

    # Default to no indicator
    return ""


def load_exclusion_periods():
    """Load exclusion periods from configuration file.

    Returns:
        tuple: (dict, pd.DatetimeIndex) containing:
            - dict: Raw exclusion periods from config
            - pd.DatetimeIndex: Pre-calculated date range for vectorized comparison
    """
    try:
        config_path = os.path.join(os.path.dirname(__file__), "exclusion_periods.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                periods = json.load(f)

            # Create a list of all exclusion dates for vectorized comparison
            all_dates = []
            for year, year_data in periods.items():
                if "december_exclusion" in year_data:
                    period = year_data["december_exclusion"]
                    start = pd.to_datetime(period["start"])
                    end = pd.to_datetime(period["end"])
                    all_dates.extend(pd.date_range(start, end))

            return periods, pd.DatetimeIndex(all_dates)
    except Exception as e:
        print(f"Error loading exclusion periods: {e}")
    return {}, pd.DatetimeIndex([])


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, "resources", relative_path)


def get_app_root():
    """Get the application root directory.

    This will be the directory containing the executable when packaged,
    or the current directory during development.

    Returns:
        str: Path to application root directory
    """
    try:
        # If running from PyInstaller bundle
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        # If running from script
        return os.path.abspath(os.path.dirname(__file__))
    except Exception:
        return os.path.abspath(".")


def get_data_path(filename):
    """Get the full path for a data file in the application root directory.

    Args:
        filename (str): Name of the file

    Returns:
        str: Full path to the data file in the application root
    """
    return os.path.join(get_app_root(), filename)


def get_user_data_dir():
    """Get the appropriate directory for user-specific data files.

    Returns:
        str: Path to user data directory
    """
    # Use AppData/Local on Windows, .local/share on Linux, or ~/Library on macOS
    if os.name == "nt":  # Windows
        base_dir = os.path.join(os.environ["LOCALAPPDATA"], "Eightbox")
    else:  # Linux/Mac
        base_dir = os.path.join(os.path.expanduser("~"), ".eightbox")

    # Create directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_user_data_path(filename):
    """Get the full path for a user-specific data file.

    Args:
        filename (str): Name of the file

    Returns:
        str: Full path to the user data file
    """
    return os.path.join(get_user_data_dir(), filename)


def ensure_app_directories():
    """Create necessary application directories if they don't exist.

    Creates:
        - backup directory
        - backups directory
        - spreadsheets directory

    Returns:
        dict: Paths to created directories
    """
    app_root = get_app_root()
    directories = {
        "backup": os.path.join(app_root, "backup"),
        "backups": os.path.join(app_root, "backups"),
        "spreadsheets": os.path.join(app_root, "spreadsheets"),
    }

    for dir_path in directories.values():
        os.makedirs(dir_path, exist_ok=True)

    return directories


def get_backup_dir():
    """Get the backup directory path, creating it if necessary."""
    backup_dir = os.path.join(get_app_root(), "backup")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def get_backups_dir():
    """Get the backups directory path, creating it if necessary."""
    backups_dir = os.path.join(get_app_root(), "backups")
    os.makedirs(backups_dir, exist_ok=True)
    return backups_dir


def get_spreadsheets_dir():
    """Get the spreadsheets directory path, creating it if necessary."""
    spreadsheets_dir = os.path.join(get_app_root(), "spreadsheets")
    os.makedirs(spreadsheets_dir, exist_ok=True)
    return spreadsheets_dir
