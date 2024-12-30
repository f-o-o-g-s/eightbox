"""Article 8.5.D violation detection and remedy calculations.

This module handles violations that occur when carriers work off their
bid assignments without proper notification.
"""

import numpy as np
import pandas as pd

from utils import set_display
from violation_formulas.formula_utils import prepare_data_for_violations


def detect_85d_violations(
    data: pd.DataFrame, date_maximized_status: dict
) -> pd.DataFrame:
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
        lambda x: (
            date_maximized_status.get(x, False) if date_maximized_status else False
        )
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
