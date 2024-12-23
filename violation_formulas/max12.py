"""Maximum 12-hour violation detection and remedy calculations.

This module handles violations that occur when carriers exceed their maximum
daily work hour limits (12 hours for most carriers, 11.5 for WAL carriers
working off assignment and NL/PTF carriers).
"""

import numpy as np
import pandas as pd

from utils import load_exclusion_periods
from violation_formulas.formula_utils import process_moves_vectorized


def detect_MAX_12(data, date_maximized_status=None):
    """Detect violations of maximum daily work hour limits.

    Args:
        data (pd.DataFrame): Carrier work hour data containing:
            - carrier_name: Name of the carrier
            - list_status: WAL/NL/OTDL/PTF status
            - total: Total hours worked
            - code: Route assignment code
            - moves: Route move history
        date_maximized_status (dict, optional): Not used for this violation type

    Returns:
        pd.DataFrame: Detected violations with calculated remedies. Contains ALL carriers,
            with appropriate max hour limits applied based on status.

    Note:
        Violation occurs when carrier exceeds their maximum daily limit:
        - WAL carriers: 11.50 hours if moved between routes, 12.00 if not
        - NL/PTF carriers: 11.50 hours
        - OTDL carriers: 12.00 hours

        December Exclusions:
        - OTDL carriers cannot trigger MAX12 violations in December
        - WAL carriers working only their assignment--
        - cannot trigger MAX12 violations in December
        - WAL carriers working off assignment--
        - CAN trigger MAX12 violations in December (treated as NL)
        - NL/PTF carriers can still trigger MAX12 violations in December

        Remedy:
        - Hours worked beyond the applicable limit (11.50/12.00)

        Processing:
        - Analyzes all carriers with appropriate limits by type
        - Considers route moves when determining WAL carrier limits
        - Maintains complete carrier roster for reporting consistency
        - Rounds remedy hours to 2 decimal places
        - Handles complex December exclusion rules by
        - carrier type and assignment
    """
    if "list_status" not in data.columns:
        raise ValueError("The 'list_status' column is missing from the data")

    # Prepare data
    result_df = data.copy()
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()
    result_df["total_hours"] = pd.to_numeric(
        result_df["total"], errors="coerce"
    ).fillna(0)

    # Process moves vectorized
    moves_result = result_df.apply(
        lambda x: process_moves_vectorized(x.get("moves", "none"), x["code"]), axis=1
    )
    result_df = pd.concat([result_df, moves_result], axis=1)

    # Convert dates to datetime for comparison
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])

    # Load exclusion periods
    exclusion_periods, all_dates = load_exclusion_periods()

    # Check for exclusion period
    def is_in_exclusion_period(date):
        return date in all_dates

    # Mark exclusion periods
    result_df["is_excluded"] = result_df["date_dt"].apply(is_in_exclusion_period)

    # Determine if WAL carriers are working off assignment
    result_df["is_working_off_assignment"] = (
        (result_df["list_status"] == "wal")
        & (result_df["moves"].notna())
        & (result_df["moves"] != "none")
        & (result_df["off_route_hours"] > 0)
    )

    # Calculate max hours based on carrier type, moves, and December exclusions
    result_df["max_hours"] = np.where(
        result_df["is_excluded"],
        # December rules
        np.where(
            result_df["list_status"] == "otdl",
            float("inf"),  # OTDL exempt in December
            np.where(
                (result_df["list_status"] == "wal")
                & ~result_df["is_working_off_assignment"],
                float("inf"),  # WAL on assignment exempt in December
                11.5,  # All others (NL, PTF, WAL off assignment) limited to 11.5
            ),
        ),
        # Non-December rules
        np.where(
            result_df["list_status"] == "wal",
            np.where(
                result_df["moves"].notna() & (result_df["moves"] != "none"), 11.5, 12.0
            ),
            np.where(result_df["list_status"].isin(["nl", "ptf"]), 11.5, 12.0),  # OTDL
        ),
    )

    # Calculate remedies vectorized
    result_df["remedy_total"] = (
        (result_df["total_hours"] - result_df["max_hours"]).clip(lower=0).round(2)
    )

    # Set violation types with appropriate messages
    result_df["violation_type"] = np.where(
        result_df["remedy_total"] > 0,
        "MAX12 More Than 12 Hours Worked in a Day",
        np.where(
            result_df["is_excluded"],
            np.where(
                result_df["list_status"] == "otdl",
                "No Violation (December Exclusion - OTDL)",
                np.where(
                    (result_df["list_status"] == "wal")
                    & ~result_df["is_working_off_assignment"],
                    "No Violation (December Exclusion - WAL On Assignment)",
                    "No Violation",
                ),
            ),
            "No Violation",
        ),
    )

    # Select and rename columns
    return result_df[
        [
            "carrier_name",
            "list_status",
            "violation_type",
            "rings_date",
            "remedy_total",
            "total_hours",
            "own_route_hours",
            "formatted_moves",
            "moves",
        ]
    ].rename(columns={"rings_date": "date", "formatted_moves": "off_route_hours"}) 