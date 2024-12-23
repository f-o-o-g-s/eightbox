"""Utility functions for violation formula calculations.

This module contains shared utility functions used by multiple violation
formula modules for data preparation, move processing, and calculations.
"""

import pandas as pd


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

    Note:
        - Handles empty/invalid move strings gracefully
        - Returns 0 hours and "No Moves" for invalid input
        - Rounds hours to 2 decimal places
        - Used by prepare_data_for_violations for move processing
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

        # Calculate off-route hours first
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
                "own_route_hours": 0.0,  # Will be calculated in prepare_data_for_violations
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


def prepare_data_for_violations(data):
    """Prepare and standardize carrier data for violation detection.

    Args:
        data (pd.DataFrame): Raw carrier work hour data

    Returns:
        pd.DataFrame: Standardized data with consistent column names and types
    """
    result_df = data.copy()

    # Convert list_status to lowercase and strip
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Create mask for WAL/NL carriers
    result_df["is_wal_nl"] = result_df["list_status"].isin(["wal", "nl"])

    # Ensure numeric columns
    result_df["total_hours"] = pd.to_numeric(
        result_df["total"], errors="coerce"
    ).fillna(0)

    # Process moves for each row
    moves_data = result_df.apply(
        lambda x: process_moves_vectorized(x.get("moves", "none"), x["code"]), axis=1
    )
    result_df[["own_route_hours", "off_route_hours", "formatted_moves"]] = moves_data

    # Calculate own_route_hours as total_hours - off_route_hours
    result_df["own_route_hours"] = (
        result_df["total_hours"] - result_df["off_route_hours"]
    ).round(2)

    # Handle OTDL/PTF carriers - all their hours count as own route
    otdl_ptf_mask = result_df["list_status"].isin(["otdl", "ptf"])
    result_df.loc[otdl_ptf_mask, "own_route_hours"] = result_df.loc[
        otdl_ptf_mask, "total_hours"
    ]
    result_df.loc[otdl_ptf_mask, "off_route_hours"] = 0.0
    result_df.loc[otdl_ptf_mask, "formatted_moves"] = "No Moves"

    return result_df
