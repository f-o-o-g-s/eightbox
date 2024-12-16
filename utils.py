"""Utility functions used throughout the application.

This module provides helper functions for data processing and display formatting.
Functions here are designed to be reusable across different parts of the application
and handle common tasks like formatting display indicators for various carrier statuses.
"""


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
