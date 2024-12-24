"""Article 8.5.F 5th violation detection and remedy calculations.

This module handles violations that occur when non-OTDL carriers work
overtime on more than 4 of their 5 scheduled days in a service week.
"""

import numpy as np
import pandas as pd

from utils import set_display
from violation_formulas.article_85f import load_exclusion_periods


def detect_85f_5th_violations(
    data: pd.DataFrame, date_maximized_status: dict
) -> pd.DataFrame:
    """Detect Article 8.5.F violations for fifth overtime day in a week.

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
            with non-eligible carriers (OTDL/PTF) marked as "No Violation"

    Note:
        Violation occurs when:
        - Carrier is WAL or NL
        - Worked overtime on 5 scheduled days in a week
        - Not during December exclusion period
    """
    # Keep all carriers but only process violations for WAL/NL
    result_df = data.copy()

    # Convert numeric columns safely
    result_df["total_hours"] = pd.to_numeric(
        result_df["total"], errors="coerce"
    ).fillna(0)
    result_df["leave_time"] = pd.to_numeric(
        result_df.get("leave_time", 0), errors="coerce"
    ).fillna(0)
    result_df["leave_type"] = result_df["leave_type"].astype(str)
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Calculate daily hours with holiday handling vectorized
    holiday_mask = (result_df["leave_type"].str.lower() == "holiday") & (
        result_df["leave_time"] == 8.00
    )
    result_df["daily_hours"] = np.where(
        holiday_mask,
        result_df["total_hours"],
        np.where(
            result_df["leave_time"] <= result_df["total_hours"],
            np.maximum(result_df["total_hours"], result_df["leave_time"]),
            result_df["total_hours"] + result_df["leave_time"],
        ),
    )

    # Add display indicators
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)

    # Convert dates to datetime for comparison
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])

    # Create service week groups (Saturday to Friday)
    result_df["service_week"] = result_df["date_dt"].dt.to_period("W-SAT")
    result_df["day_of_week"] = result_df["date_dt"].dt.dayofweek  # Monday=0, Sunday=6

    # Load exclusion periods and get pre-calculated date range
    _, exclusion_dates = load_exclusion_periods()

    # Vectorized exclusion period check
    result_df["is_excluded"] = result_df["date_dt"].isin(exclusion_dates)

    # Process all carriers but only calculate violations for WAL/NL
    base_result = []
    for carrier in result_df["carrier_name"].unique():
        carrier_data = result_df[result_df["carrier_name"] == carrier].sort_values(
            "date_dt"
        )
        list_status = carrier_data["list_status"].iloc[0]
        is_eligible = list_status in ["wal", "nl"]

        # Skip if not eligible or in exclusion period
        if not is_eligible or carrier_data["is_excluded"].any():
            for _, day in carrier_data.iterrows():
                base_result.append(
                    {
                        "carrier_name": carrier,
                        "date": day["rings_date"],
                        "list_status": day["list_status"],
                        "violation_type": "No Violation (December Exclusion)"
                        if day["is_excluded"]
                        else "No Violation",
                        "remedy_total": 0.0,
                        "total_hours": day["daily_hours"],
                        "display_indicator": day["display_indicator"],
                        "85F_5th_date": "",
                    }
                )
            continue

        # Check for 8-hour days (excluding Sundays)
        non_sunday_mask = carrier_data["day_of_week"] != 6
        worked_day_mask = carrier_data["daily_hours"] > 0
        had_eight_hour_day = (
            carrier_data[non_sunday_mask & worked_day_mask]["daily_hours"]
            .between(0.01, 8.00, inclusive="both")
            .any()
        )

        if had_eight_hour_day:
            # No violation if carrier had an 8-hour day
            for _, day in carrier_data.iterrows():
                base_result.append(
                    {
                        "carrier_name": carrier,
                        "date": day["rings_date"],
                        "list_status": day["list_status"],
                        "violation_type": "No Violation",
                        "remedy_total": 0.0,
                        "total_hours": day["daily_hours"],
                        "display_indicator": day["display_indicator"],
                        "85F_5th_date": "",
                    }
                )
            continue

        # Find potential violation days
        overtime_days = carrier_data[
            (carrier_data["day_of_week"] != 6)  # Exclude Sundays
            & (carrier_data["daily_hours"] > 8)
            & (
                ~carrier_data["code"].str.contains("ns day", case=False, na=False)
            )  # Exclude non-scheduled days
        ].sort_values("date_dt")

        violation_date = None
        if len(overtime_days) >= 5:
            # Get the 5th overtime day in sequence
            violation_date = overtime_days.iloc[4]["rings_date"]

        # Add all days for this carrier
        for _, day in carrier_data.iterrows():
            # Extract just the date part for comparison by splitting on space
            day_date = (
                day["rings_date"].split(" ")[0]
                if isinstance(day["rings_date"], str)
                else day["rings_date"]
            )
            is_violation = day_date == violation_date

            base_result.append(
                {
                    "carrier_name": carrier,
                    "date": day["rings_date"],
                    "list_status": day["list_status"],
                    "violation_type": "8.5.F 5th More Than 4 Days of Overtime in a Week"
                    if is_violation
                    else "No Violation",
                    "remedy_total": round(max(0, day["daily_hours"] - 8), 2)
                    if is_violation
                    else 0.0,
                    "total_hours": day["daily_hours"],
                    "display_indicator": day["display_indicator"],
                    "85F_5th_date": violation_date if is_violation else "",
                }
            )

    # Convert to DataFrame and ensure all required columns are present
    result_df = pd.DataFrame(base_result)
    required_columns = [
        "carrier_name",
        "list_status",
        "violation_type",
        "date",
        "remedy_total",
        "total_hours",
        "display_indicator",
        "85F_5th_date",
    ]

    # Return DataFrame with columns in the expected order
    return result_df[required_columns]
