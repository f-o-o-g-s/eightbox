"""Maximum 60-hour violation detection and remedy calculations.

This module handles violations that occur when carriers exceed their maximum
weekly work hour limit of 60 hours.
"""

import numpy as np
import pandas as pd

from utils import load_exclusion_periods, set_display


def detect_MAX_60(data, date_maximized_status=None):
    """Detect violations of maximum weekly work hour limits.

    Args:
        data (pd.DataFrame): Carrier work hour data containing:
            - carrier_name: Name of the carrier
            - list_status: WAL/NL/OTDL status
            - total_hours: Total hours worked
            - leave_time: Hours of paid leave
            - leave_type: Type of leave (e.g., holiday, annual)
            - date: Date of potential violation
        date_maximized_status (dict, optional): Not used for this violation type

    Returns:
        pd.DataFrame: Detected violations with calculated remedies. Contains ALL carriers,
            with non-eligible carriers (PTF) marked as "No Violation"

    Note:
        Violation occurs when:
        - Carrier's total weekly hours exceed 60
        - Carrier is WAL, NL, or OTDL (PTFs exempt)
        - Not during December exclusion period (varies by year, defined in exclusion_periods.json)
          as no carriers are subject to the 60-hour limit during December in Billings, MT

        Weekly hours include:
        - Regular work hours
        - Paid leave hours
        - Holiday pay hours

        Remedy:
        - All hours worked beyond 60 in the service week

        Processing:
        - Analyzes all carriers except PTFs
        - Aggregates hours across entire service week
        - Considers all forms of paid time toward 60-hour limit
        - Maintains complete carrier roster for reporting consistency
        - Rounds remedy hours to 2 decimal places
        - December exclusion applies to all carriers
    """
    # Keep all carriers but mark eligible ones
    result_df = data.copy()
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Convert numeric columns for all carriers
    numeric_cols = ["total", "leave_time"]
    for col in numeric_cols:
        result_df[col] = pd.to_numeric(result_df[col], errors="coerce").fillna(0)

    # Calculate daily hours vectorized for all carriers
    result_df["daily_hours"] = np.where(
        result_df["leave_time"] <= result_df["total"],
        result_df[["total", "leave_time"]].max(axis=1),
        result_df["total"] + result_df["leave_time"],
    )

    # Convert dates to datetime for comparison
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])

    # Load exclusion periods
    exclusion_periods, all_dates = load_exclusion_periods()

    # Check for exclusion period
    def is_in_exclusion_period(date):
        return date in all_dates

    # Mark exclusion periods
    result_df["is_excluded"] = result_df["date_dt"].apply(is_in_exclusion_period)

    # Group by carrier and date
    daily_totals = (
        result_df.groupby(["carrier_name", "rings_date", "date_dt"])
        .agg(
            {
                "daily_hours": "sum",
                "list_status": "first",
                "leave_type": "first",
                "code": "first",
                "total": "sum",
                "leave_time": "sum",
                "is_excluded": "first",
            }
        )
        .reset_index()
    )

    # Calculate display indicators vectorized
    daily_totals["display_indicator"] = daily_totals.apply(set_display, axis=1)

    # Calculate cumulative hours for all carriers
    daily_totals["cumulative_hours"] = daily_totals.groupby("carrier_name")[
        "daily_hours"
    ].cumsum()

    # Initialize remedy_total
    daily_totals["remedy_total"] = 0.0

    # Calculate violations vectorized only for eligible carriers
    grouped = daily_totals.groupby("carrier_name")
    last_day_mask = grouped["rings_date"].transform("max") == daily_totals["rings_date"]
    over_60_mask = daily_totals["cumulative_hours"] > 60.0

    # All carriers are exempt from 60-hour limit during December
    # Only check for violations outside the exclusion period
    eligible_mask = (
        daily_totals["list_status"].isin(["wal", "nl", "otdl"])
        & ~daily_totals[  # All regular carriers
            "is_excluded"
        ]  # Not in December exclusion period
    )

    # Set violation types and remedies
    daily_totals.loc[last_day_mask & over_60_mask & eligible_mask, "remedy_total"] = (
        daily_totals.loc[
            last_day_mask & over_60_mask & eligible_mask, "cumulative_hours"
        ]
        - 60.0
    ).round(2)

    # Set violation types with December exclusion note
    daily_totals["violation_type"] = "No Violation"
    daily_totals.loc[
        last_day_mask & over_60_mask & eligible_mask, "violation_type"
    ] = "MAX60 More Than 60 Hours Worked in a Week"
    daily_totals.loc[
        daily_totals["is_excluded"]
        & daily_totals["list_status"].isin(["wal", "nl", "otdl"]),
        "violation_type",
    ] = "No Violation (December Exclusion)"

    # Rename date column for consistency
    result = daily_totals.rename(columns={"rings_date": "date"})

    # Fill missing values
    result = result.fillna(
        {
            "list_status": "unknown",
            "violation_type": "No Violation",
            "remedy_total": 0.0,
            "daily_hours": 0.0,
            "cumulative_hours": 0.0,
            "display_indicator": "",
        }
    )

    return result[
        [
            "carrier_name",
            "list_status",
            "violation_type",
            "date",
            "remedy_total",
            "daily_hours",
            "cumulative_hours",
            "display_indicator",
        ]
    ] 