"""Article 8.5.F NS violation detection and remedy calculations.

This module handles violations that occur when non-OTDL carriers work
more than 8 hours on their non-scheduled day.
"""

import numpy as np
import pandas as pd

from utils import set_display
from violation_formulas.article_85f import load_exclusion_periods


def detect_85f_ns_violations(data: pd.DataFrame, date_maximized_status: dict) -> pd.DataFrame:
    """Detect Article 8.5.F violations for overtime on non-scheduled days.

    Args:
        data (pd.DataFrame): Carrier work hour data containing:
            - carrier_name: Name of the carrier
            - list_status: WAL/NL/OTDL status
            - total_hours: Total hours worked
            - code: Route assignment code (to identify NS days)
            - date: Date of potential violation
        date_maximized_status (dict, optional): Not used for this violation type

    Returns:
        pd.DataFrame: Detected violations with calculated remedies. Contains ALL carriers,
            with non-eligible carriers (OTDL/PTF) marked as "No Violation"

    Note:
        Violation occurs when:
        - Carrier is WAL or NL
        - Working on their non-scheduled day
        - Worked more than 8 hours that day
        - Not during December exclusion period
    """
    # Set the pandas option to opt-in to the future behavior
    pd.set_option("future.no_silent_downcasting", True)

    result_df = data.copy()

    # Handle empty DataFrame
    if result_df.empty:
        return pd.DataFrame(
            columns=[
                "carrier_name",
                "list_status",
                "violation_type",
                "date",
                "remedy_total",
                "total_hours",
                "display_indicator",
            ]
        )

    # Prepare data
    result_df["total_hours"] = pd.to_numeric(
        result_df["total"], errors="coerce"
    ).fillna(0)
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Update code column handling with the new pandas behavior
    result_df["code"] = result_df["code"].fillna("").astype(str)

    # Check for NS day in code
    result_df["is_ns_day"] = (
        result_df["code"].str.strip().str.lower().str.contains("ns day", na=False)
    )

    # Convert dates to datetime for comparison
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])

    # Load exclusion periods and get pre-calculated date range
    _, exclusion_dates = load_exclusion_periods()

    # Vectorized exclusion period check
    result_df["is_excluded"] = result_df["date_dt"].isin(exclusion_dates)

    # Set exclusion period entries first
    result_df.loc[
        result_df["is_excluded"], "violation_type"
    ] = "No Violation (December Exclusion)"
    result_df.loc[result_df["is_excluded"], "remedy_total"] = 0.0

    # Calculate violations vectorized using conditions directly
    result_df["remedy_total"] = np.where(
        (result_df["list_status"].isin(["wal", "nl"]))
        & (result_df["is_ns_day"])
        & ~result_df["is_excluded"],
        (result_df["total_hours"] - 8).clip(lower=0).round(2),
        result_df["remedy_total"] if "remedy_total" in result_df.columns else 0.0,
    )

    # Set violation types
    result_df["violation_type"] = np.where(
        ~result_df["is_excluded"] & (result_df["remedy_total"] > 0),
        "8.5.F NS Overtime On a Non-Scheduled Day",
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
            "total_hours",
            "display_indicator",
        ]
    ].rename(columns={"rings_date": "date"}) 