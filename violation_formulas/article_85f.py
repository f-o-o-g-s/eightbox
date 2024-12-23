"""Article 8.5.F violation detection and remedy calculations.

This module handles violations that occur when non-OTDL carriers work
more than 10 hours on a regularly scheduled day.
"""

import json
import os

import numpy as np
import pandas as pd

from utils import set_display
from violation_formulas.formula_utils import prepare_data_for_violations


def detect_85f_violations(
    data: pd.DataFrame, date_maximized_status: dict
) -> pd.DataFrame:
    """Detect Article 8.5.F violations for work over 10 hours off assignment.

    Args:
        data (pd.DataFrame): Carrier work hour data containing:
            - carrier_name: Name of the carrier
            - list_status: WAL/NL/OTDL status
            - total_hours: Total hours worked
            - off_route_hours: Hours worked off assignment
            - date: Date of potential violation
        date_maximized_status (dict, optional): Not used for this violation type

    Returns:
        pd.DataFrame: Detected violations with calculated remedies. Contains ALL carriers,
            with non-eligible carriers (OTDL/PTF) marked as "No Violation"

    Note:
        Violation occurs when:
        - Carrier is WAL or NL
        - Worked more than 10 hours in a day
        - Some portion was worked off assignment
        - Not during December exclusion period
    """
    # Use the same data preparation as 8.5.D
    result_df = prepare_data_for_violations(data)

    # Convert dates to datetime for comparison
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])

    # Load exclusion periods and get pre-calculated date range
    _, exclusion_dates = load_exclusion_periods()

    # Vectorized exclusion period check
    result_df["is_excluded"] = result_df["date_dt"].isin(exclusion_dates)

    # Set exclusion period entries
    result_df.loc[
        result_df["is_excluded"], "violation_type"
    ] = "No Violation (December Exclusion)"
    result_df.loc[result_df["is_excluded"], "remedy_total"] = 0.0

    # Calculate remedies vectorized for all non-excluded carriers
    mask_eligible = result_df["is_wal_nl"] & ~result_df["is_excluded"]
    result_df["remedy_total"] = np.where(
        mask_eligible & (result_df["total_hours"] > 10),
        np.minimum(
            result_df["off_route_hours"], (result_df["total_hours"] - 10).clip(lower=0)
        ),
        result_df["remedy_total"] if "remedy_total" in result_df.columns else 0.0,
    )

    # Set violation types for non-excluded dates
    result_df["violation_type"] = np.where(
        ~result_df["is_excluded"] & (result_df["remedy_total"] > 0),
        "8.5.F Overtime Over 10 Hours Off Route",
        result_df["violation_type"]
        if "violation_type" in result_df.columns
        else "No Violation",
    )

    # Add display indicator
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)

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


def load_exclusion_periods():
    """Load exclusion periods from configuration file.

    Returns:
        tuple: (dict, pd.DatetimeIndex) containing:
            - dict: Raw exclusion periods from config
            - pd.DatetimeIndex: Pre-calculated date range for vectorized comparison
    """
    try:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "exclusion_periods.json"
        )
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
