"""Utility functions used throughout the application.

Contains helper functions and common utilities that are used by multiple
modules across the application for data processing and manipulation.
"""


def set_display(row):
    """Set display indicators based on conditions."""
    code = (
        str(row.get("code", "")).strip().lower()
    )  # Use .get to avoid KeyError if column is missing
    leave_type = str(row.get("leave_type", "")).strip().lower()

    # Check for specific leave indicators
    if code == "annual" and leave_type == "none":
        return "(NS protect)"
    elif code == "annual" and leave_type == "annual":
        return "(annual)"
    elif code == "none" and leave_type == "annual":
        return "(annual)"
    elif code == "none" and leave_type == "guaranteed":
        return "(guaranteed)"
    elif code == "none" and leave_type == "holiday":
        return "(holiday)"
    elif code == "ns day" and leave_type == "none":
        return "(NS day)"
    elif code == "sick" and leave_type == "sick":
        return "(sick)"
    elif code == "none" and leave_type == "sick":
        return "(sick)"
    elif code == "no call" and leave_type == "none":
        return "(no call)"

    # Default to no indicator
    return ""
