"""Article 8.5.D violation detection and remedy calculations.

This module handles violations that occur when carriers work off their
bid assignments without proper notification.
"""

import numpy as np
import pandas as pd

from utils import set_display


def prepare_data_for_violations(data):
    """Prepare and standardize carrier data for violation detection."""
    result_df = data.copy()

    # Convert list_status to lowercase and strip
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Create mask for WAL/NL carriers
    result_df["is_wal_nl"] = result_df["list_status"].isin(["wal", "nl"])

    # Ensure numeric columns
    result_df["total_hours"] = pd.to_numeric(
        result_df["total"], errors="coerce"
    ).fillna(0)

    # Initialize hours columns
    result_df["own_route_hours"] = 0.0
    result_df["off_route_hours"] = 0.0

    # Process moves for each row
    moves_data = result_df.apply(process_moves_row, axis=1)
    result_df[["own_route_hours", "off_route_hours", "formatted_moves"]] = moves_data

    # Handle OTDL/PTF carriers - all their hours count as own route
    otdl_ptf_mask = result_df["list_status"].isin(["otdl", "ptf"])
    result_df.loc[otdl_ptf_mask, "own_route_hours"] = result_df.loc[
        otdl_ptf_mask, "total_hours"
    ]
    result_df.loc[otdl_ptf_mask, "off_route_hours"] = 0.0
    result_df.loc[otdl_ptf_mask, "formatted_moves"] = "No Moves"

    return result_df


def process_moves_row(row):
    """Process route moves and calculate hours by assignment for a single carrier row."""
    if not isinstance(row["moves"], str) or row["moves"].strip().lower() == "none":
        return pd.Series(
            {
                "own_route_hours": row[
                    "total_hours"
                ],  # All hours go to own route if no moves
                "off_route_hours": 0.0,
                "formatted_moves": "No Moves",
            }
        )

    own_hours = 0.0
    off_hours = 0.0

    try:
        moves_segments = row["moves"].split(",")
        for i in range(0, len(moves_segments), 3):
            start_time = float(moves_segments[i].strip())
            end_time = float(moves_segments[i + 1].strip())
            route = moves_segments[i + 2].strip()
            hours = max(0, end_time - start_time)

            if route.lower() == row["code"].lower():
                own_hours += hours
            else:
                off_hours += hours

        # Add remaining time to own_route_hours
        remaining_hours = max(0, row["total_hours"] - (own_hours + off_hours))
        own_hours += remaining_hours

        return pd.Series(
            {
                "own_route_hours": round(own_hours, 2),
                "off_route_hours": round(off_hours, 2),
                "formatted_moves": process_moves_vectorized(row["moves"], row["code"])[
                    "formatted_moves"
                ],
            }
        )
    except (ValueError, IndexError):
        return pd.Series(
            {
                "own_route_hours": row[
                    "total_hours"
                ],  # Default to all hours as own route
                "off_route_hours": 0.0,
                "formatted_moves": "No Moves",
            }
        )


def process_moves_vectorized(moves_str, code):
    """Process carrier route moves and calculate hours by assignment.

    Args:
        moves_str (str): Comma-separated move entries in format "start,end,route"
        code (str): Carrier's assigned route code

    Returns:
        pd.Series: Contains:
            - own_route_hours (float): Hours worked on assigned route
            - off_route_hours (float): Hours worked on other routes
            - formatted_moves (str): Human-readable move summary
    """
    if not isinstance(moves_str, str) or moves_str.strip().lower() in [
        "none",
        "",
        "no moves",
    ]:
        return pd.Series(
            {
                "own_route_hours": 0.0,
                "off_route_hours": 0.0,
                "formatted_moves": "No Moves",
            }
        )

    try:
        moves = pd.DataFrame([x.strip() for x in moves_str.split(",")]).values.reshape(
            -1, 3
        )

        moves_df = pd.DataFrame(moves, columns=["start", "end", "route"])
        moves_df[["start", "end"]] = moves_df[["start", "end"]].astype(float)
        moves_df["hours"] = (moves_df["end"] - moves_df["start"]).clip(lower=0)

        own_route = moves_df[moves_df["route"].str.lower() == code.lower()][
            "hours"
        ].sum()
        off_route = moves_df[moves_df["route"].str.lower() != code.lower()][
            "hours"
        ].sum()

        # Format moves for display
        formatted = moves_df.groupby("route")["hours"].sum().round(2)
        formatted_str = "\n".join(
            f"rt{route} {hours}" for route, hours in formatted.items()
        )

        return pd.Series(
            {
                "own_route_hours": own_route,
                "off_route_hours": off_route,
                "formatted_moves": formatted_str if formatted_str else "No Moves",
            }
        )
    except (ValueError, IndexError):
        return pd.Series(
            {
                "own_route_hours": 0.0,
                "off_route_hours": 0.0,
                "formatted_moves": "No Moves",
            }
        )


def detect_85d_violations(data: pd.DataFrame, date_maximized_status: dict) -> pd.DataFrame:
    """Detect Article 8.5.D violations for working off bid assignment.

    Args:
        data: DataFrame containing carrier clock rings and moves
        date_maximized_status: Dictionary of violation detection settings

    Returns:
        DataFrame containing detected violations with remedy calculations
    """
    result_df = prepare_data_for_violations(data)

    # Check for NS day in code
    result_df["is_ns_day"] = (
        result_df["code"].str.strip().str.lower().str.contains("ns day", na=False)
    )

    # Initialize violation_type column with "No Violation"
    result_df["violation_type"] = "No Violation"

    # Handle maximized dates
    maximized_dates = result_df["rings_date"].map(
        lambda x: date_maximized_status.get(x, False)
        if date_maximized_status
        else False
    )

    # Set "No Violation (OTDL Maxed)" for maximized dates
    result_df.loc[maximized_dates, "violation_type"] = "No Violation (OTDL Maxed)"

    # Add display indicator
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)

    # Check for valid moves (not empty, none, or no moves)
    has_valid_moves = (
        result_df["moves"].notna()
        & (result_df["moves"].str.strip().str.lower() != "none")
        & (result_df["moves"].str.strip() != "")
        & (result_df["moves"].str.strip().str.lower() != "no moves")
    )

    # Calculate eligible carriers - require moves only for non-NS days
    mask_eligible = (
        (result_df["is_wal_nl"])
        & (~maximized_dates)
        & (result_df["is_ns_day"] | has_valid_moves)
    )

    # Vectorized remedy calculation - different for NS days
    result_df["remedy_total"] = np.where(
        mask_eligible & result_df["is_ns_day"],
        result_df["total_hours"].round(2),  # Full hours for NS days
        np.where(
            mask_eligible,
            np.minimum(
                result_df["off_route_hours"],
                (result_df["total_hours"] - 8).clip(lower=0),
            ),
            0.0,
        ),
    )

    # Set violation types for non-maximized dates with violations
    mask_has_violation = (result_df["remedy_total"] > 0) & (~maximized_dates)
    result_df.loc[mask_has_violation, "violation_type"] = "8.5.D Overtime Off Route"

    return result_df[
        [
            "carrier_name",
            "list_status",
            "violation_type",
            "rings_date",
            "remedy_total",
            "own_route_hours",
            "formatted_moves",
            "total_hours",
            "moves",
            "display_indicator",
        ]
    ].rename(columns={"rings_date": "date", "formatted_moves": "off_route_hours"}) 