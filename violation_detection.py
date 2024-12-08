"""Implements violation detection logic for carrier work hours.

Contains the core algorithms and rules for detecting various types of
work hour violations based on carrier schedules and USPS regulations.
"""

# violation_detection.py
from typing import (
    Callable,
    Dict,
    Optional,
)

import numpy as np
import pandas as pd

from utils import set_display

# Type alias for violation detection function
ViolationFunc = Callable[[pd.DataFrame, Optional[dict]], pd.DataFrame]

# Registry for violation detection functions
registered_violations: Dict[str, ViolationFunc] = {}
violation_registry: Dict[str, ViolationFunc] = {}


def register_violation(violation_type: str) -> Callable[[ViolationFunc], ViolationFunc]:
    """Register a violation detection function for a specific violation type.

    Decorator that adds the decorated function to the violation registry,
    allowing it to be called through the detect_violations dispatcher.

    Args:
        violation_type (str): Unique identifier for the violation type
            (e.g., "8.5.F NS", "MAX60", "MAX12")

    Returns:
        Callable: Decorator function that registers the violation detection function

    Example:
        @register_violation("8.5.F NS")
        def detect_85f_ns_overtime(data, date_maximized_status=None):
            # Violation detection logic
            return violation_data
    """

    def decorator(func: ViolationFunc) -> ViolationFunc:
        violation_registry[violation_type] = func
        return func

    return decorator


def detect_violations(data, violation_type, maximized_status={}):
    """Dispatch violation detection to the appropriate registered function.

    Args:
        data (pd.DataFrame): Carrier work hour data to check for violations
        violation_type (str): Type of violation to detect (e.g., "8.5.F NS", "MAX60")
        maximized_status (dict, optional): Date-keyed dict of OTDL maximization status

    Returns:
        pd.DataFrame: Detected violations with calculated remedies

    Note:
        Uses the violation registry populated by @register_violation decorator
        to route detection to the appropriate specialized function.
    """
    violation_function = violation_registry[violation_type]
    return violation_function(data, maximized_status)


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


def get_violation_remedies(data, violations):
    """Aggregate remedy hours across multiple violation types.

    Vectorized function to combine remedy hours from different violation
    types for each carrier/date combination.

    Args:
        data (pd.DataFrame): Original carrier work hour data
        violations (dict): Violation type to violation DataFrame mapping

    Returns:
        pd.DataFrame: Pivoted remedy data with:
            - Carrier and list status columns
            - Date and violation type columns
            - Aggregated remedy hours

    Note:
        - Handles empty violation data gracefully
        - Combines multiple violations for same carrier/date
        - Returns empty DataFrame with correct columns if no violations
    """
    if not violations:
        return pd.DataFrame(
            columns=[
                "date",
                "carrier_name",
                "list_status",
                "remedy_total",
                "violation_type",
            ]
        )

    # Process all violations at once
    remedy_dfs = []
    for violation_type, violation_data in violations.items():
        if not violation_data.empty:
            grouped = violation_data.groupby(["date", "carrier_name", "list_status"])[
                "remedy_total"
            ].sum()
            remedy_df = grouped.reset_index()
            remedy_df["violation_type"] = violation_type
            remedy_dfs.append(remedy_df)

    if not remedy_dfs:
        return pd.DataFrame(
            columns=[
                "date",
                "carrier_name",
                "list_status",
                "remedy_total",
                "violation_type",
            ]
        )

    # Combine all remedies
    remedy_data = pd.concat(remedy_dfs, ignore_index=True)

    # Create pivot table in one operation
    pivot_remedy_data = remedy_data.pivot_table(
        index=["carrier_name", "list_status"],
        columns=["date", "violation_type"],
        values="remedy_total",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    return pivot_remedy_data


@register_violation("8.5.D Overtime Off Route")
def detect_85d_overtime(data, date_maximized_status=None):
    """Detect Article 8.5.D violations for overtime worked off assignment.

    Args:
        data (pd.DataFrame): Carrier work hour data containing:
            - carrier_name: Name of the carrier
            - list_status: WAL/NL/OTDL status
            - total_hours: Total hours worked
            - off_route_hours: Hours worked off assignment
            - date: Date of potential violation
        date_maximized_status (dict, optional): Date-keyed dict indicating if OTDL was maximized

    Returns:
        pd.DataFrame: Detected violations with calculated remedies. Contains ALL carriers,
            with non-eligible carriers (OTDL/PTF) marked as "No Violation"

    Note:
        Violation occurs when:
        - Carrier is WAL or NL
        - Worked overtime off their assignment
        - OTDL was not maximized that day

        Remedy is lesser of:
        - Overtime hours worked (total - 8)
        - Hours worked off assignment

        Processing:
        - Analyzes all carriers but only applies violation logic to WAL/NL
        - OTDL and PTF carriers are included in output but marked as "No Violation"
        - Maintains complete carrier roster for reporting consistency
    """
    result_df = prepare_data_for_violations(data)

    # Check for NS day in code
    result_df["is_ns_day"] = (
        result_df["code"].str.strip().str.lower().str.contains("ns day", na=False)
    )

    # Handle maximized dates
    maximized_dates = result_df["rings_date"].map(
        lambda x: date_maximized_status.get(x, False)
        if date_maximized_status
        else False
    )
    result_df.loc[maximized_dates, "violation_type"] = "No Violation (OTDL Maxed)"

    # Add display indicator
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)

    # Calculate eligible carriers (WAL/NL and not maximized)
    mask_eligible = (result_df["is_wal_nl"]) & (~maximized_dates)

    # Vectorized remedy calculation - different for NS days
    result_df["remedy_total"] = np.where(
        mask_eligible & result_df["is_ns_day"],
        result_df["total_hours"].round(2),  # Full hours for NS days
        np.where(
            mask_eligible,
            np.minimum(
                result_df["off_route_hours"],
                (result_df["total_hours"] - 8).clip(lower=0),
            ).round(2),
            0.0,
        ),
    )

    # Set violation types using numpy where
    result_df.loc[~maximized_dates, "violation_type"] = np.where(
        result_df["remedy_total"] > 0, "8.5.D Overtime Off Route", "No Violation"
    )

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


@register_violation("8.5.F Overtime Over 10 Hours Off Route")
def detect_85f_overtime_over_10_hours(data, date_maximized_status=None):
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
        - Not during December

        Remedy is lesser of:
        - Hours worked over 10
        - Hours worked off assignment

        Processing:
        - Analyzes all carriers but only applies violation logic to WAL/NL
        - OTDL and PTF carriers are included in output but marked as "No Violation"
        - Maintains complete carrier roster for reporting consistency
    """
    # Use the same data preparation as 8.5.D
    result_df = prepare_data_for_violations(data)

    # Calculate remedies vectorized for all carriers
    mask_eligible = result_df["is_wal_nl"]
    result_df["remedy_total"] = np.where(
        mask_eligible & (result_df["total_hours"] > 10),
        np.minimum(
            result_df["off_route_hours"],
            (result_df["total_hours"] - 10).clip(lower=0),
        ).round(2),
        0.0,
    )

    result_df["violation_type"] = np.where(
        result_df["remedy_total"] > 0,
        "8.5.F Overtime Over 10 Hours Off Route",
        "No Violation",
    )

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
        ]
    ].rename(columns={"rings_date": "date", "formatted_moves": "off_route_hours"})


@register_violation("8.5.F 5th More Than 4 Days of Overtime in a Week")
def detect_85f_5th_overtime_over_more_than_4(data, date_maximized_status=None):
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
        - Already worked overtime on 4 other days this service week
        - Required to work overtime on a 5th day
        - No days with 0.01-8.00 hours worked (excluding Sundays)
        - Not during December

        Remedy:
        - All overtime hours worked on the 5th day (hours beyond 8)

        Processing:
        - Analyzes all carriers but only applies violation logic to WAL/NL
        - Tracks cumulative overtime days per service week
        - Considers paid leave in daily hour calculations
        - Maintains complete carrier roster for reporting consistency
    """
    # Keep all carriers but only process violations for WAL/NL
    result_df = data.copy()
    result_df["leave_time"] = pd.to_numeric(
        result_df.get("leave_time", 0), errors="coerce"
    ).fillna(0)
    result_df["leave_type"] = result_df["leave_type"].astype(str)
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Calculate daily hours with holiday handling
    holiday_mask = (result_df["leave_type"].str.lower() == "holiday") & (
        result_df["leave_time"] == 8.00
    )
    result_df["daily_hours"] = np.where(
        holiday_mask,
        result_df["total"],
        np.where(
            result_df["leave_time"] <= result_df["total"],
            np.maximum(result_df["total"], result_df["leave_time"]),
            result_df["total"] + result_df["leave_time"],
        ),
    )

    # Add display indicators
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)

    # Process all carriers but only calculate violations for WAL/NL
    base_result = []
    for carrier in result_df["carrier_name"].unique():
        carrier_data = result_df[result_df["carrier_name"] == carrier].sort_values(
            "rings_date"
        )
        list_status = carrier_data["list_status"].iloc[0]
        is_eligible = list_status in ["wal", "nl"]

        violation_date = None
        if is_eligible:
            # Only check for violations if carrier is WAL/NL
            non_sunday_mask = (
                pd.to_datetime(carrier_data["rings_date"]).dt.dayofweek != 6
            )
            worked_day_mask = carrier_data["daily_hours"] > 0
            had_eight_hour_day = (
                carrier_data[non_sunday_mask & worked_day_mask]["daily_hours"]
                .between(0.01, 8.00, inclusive="both")
                .any()
            )

            days_worked = (carrier_data["daily_hours"] > 0).cumsum()
            days_over_8 = (carrier_data["daily_hours"] > 8).cumsum()

            if not had_eight_hour_day:
                violation_mask = (days_worked > 4) & (days_over_8 > 4)
                if violation_mask.any():
                    violation_day = carrier_data[violation_mask].iloc[0]
                    violation_date = violation_day["rings_date"]

        # Add all days for this carrier
        for _, day in carrier_data.iterrows():
            is_violation = is_eligible and day["rings_date"] == violation_date
            base_result.append(
                {
                    "carrier_name": carrier,
                    "date": day["rings_date"],
                    "list_status": day["list_status"],
                    "violation_type": (
                        "8.5.F 5th More Than 4 Days of Overtime in a Week"
                        if is_violation
                        else "No Violation"
                    ),
                    "remedy_total": (
                        round(max(0, day["daily_hours"] - 8), 2)
                        if is_violation
                        else 0.0
                    ),
                    "total_hours": day["daily_hours"],
                    "display_indicator": day["display_indicator"],
                    "85F_5th_date": violation_date if is_violation else "",
                }
            )

    return pd.DataFrame(base_result).sort_values(["date", "carrier_name"])


@register_violation("MAX12 More Than 12 Hours Worked in a Day")
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

        Remedy:
        - Hours worked beyond the applicable limit (11.50/12.00)

        Processing:
        - Analyzes all carriers with appropriate limits by type
        - Considers route moves when determining WAL carrier limits
        - Maintains complete carrier roster for reporting consistency
        - Rounds remedy hours to 2 decimal places
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

    # Calculate max hours based on carrier type and moves
    result_df["max_hours"] = np.where(
        result_df["list_status"] == "wal",
        np.where(
            result_df["moves"].notna() & (result_df["moves"] != "none"), 11.5, 12.0
        ),
        np.where(result_df["list_status"].isin(["nl", "ptf"]), 11.5, 12.0),
    )

    # Calculate remedies vectorized
    result_df["remedy_total"] = (
        (result_df["total_hours"] - result_df["max_hours"]).clip(lower=0).round(2)
    )

    # Set violation types
    result_df["violation_type"] = np.where(
        result_df["remedy_total"] > 0,
        "MAX12 More Than 12 Hours Worked in a Day",
        "No Violation",
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


@register_violation("MAX60 More Than 60 Hours Worked in a Week")
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
        - Not during December

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

    # Group by carrier and date
    daily_totals = (
        result_df.groupby(["carrier_name", "rings_date"])
        .agg(
            {
                "daily_hours": "sum",
                "list_status": "first",
                "leave_type": "first",
                "code": "first",
                "total": "sum",
                "leave_time": "sum",
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
    eligible_mask = daily_totals["list_status"].isin(["wal", "nl", "otdl"])

    daily_totals.loc[last_day_mask & over_60_mask & eligible_mask, "remedy_total"] = (
        daily_totals.loc[
            last_day_mask & over_60_mask & eligible_mask, "cumulative_hours"
        ]
        - 60.0
    ).round(2)

    # Set violation types
    daily_totals["violation_type"] = np.where(
        daily_totals["remedy_total"] > 0,
        "MAX60 More Than 60 Hours Worked in a Week",
        "No Violation",
    )

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

    return result


def prepare_data_for_violations(data):
    """Prepare and standardize carrier data for violation detection.

    Args:
        data (pd.DataFrame): Raw carrier work hour data containing:
            - carrier_name: Name of carrier
            - list_status: WAL/NL/OTDL/PTF status
            - total: Total hours worked
            - code: Route assignment code
            - moves: Route move history

    Returns:
        pd.DataFrame: Processed data frame with:
            - Standardized column names and types
            - Calculated own_route_hours and off_route_hours
            - Formatted move summaries
            - is_wal_nl and is_otdl_ptf flags
            - All numeric fields converted and validated

    Note:
        - Handles data preparation for ALL carriers regardless of status
        - Special processing for OTDL/PTF carriers (all hours as own route)
        - Used by multiple violation detectors to ensure consistent processing
        - Maintains complete carrier roster for reporting consistency
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

    # Initialize hours columns
    result_df["own_route_hours"] = 0.0
    result_df["off_route_hours"] = 0.0

    # Process moves for each row
    def process_moves_row(row):
        """Process route moves and calculate hours by assignment for a single carrier row.

        Args:
            row (pd.Series): Single row of carrier data containing:
                - moves: Comma-separated move entries ("start,end,route,...")
                - code: Carrier's assigned route code
                - total_hours: Total hours worked

        Returns:
            pd.Series: Contains:
                - own_route_hours (float): Hours worked on assigned route
                - off_route_hours (float): Hours worked on other routes
                - formatted_moves (str): Human-readable move summary

        Note:
            - Handles empty/invalid move strings by assigning all hours to own route
            - Processes move segments in groups of 3 (start, end, route)
            - Rounds hours to 2 decimal places
            - Used internally by prepare_data_for_violations
            - Special case: Returns all hours as own_route if moves is "none"
        """
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
                    "formatted_moves": process_moves_vectorized(
                        row["moves"], row["code"]
                    )["formatted_moves"],
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

    # Apply the moves processing
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


def detect_violations_optimized(clock_ring_data):
    """Process all violation types in a single optimized pass.

    Args:
        clock_ring_data (pd.DataFrame): Raw carrier clock ring data

    Returns:
        dict: Violation type to DataFrame mapping containing:
            - 8.5.D violations
            - 8.5.F violations
            - 8.5.F NS violations
            - 8.5.F 5th day violations
            - MAX12 violations
            - MAX60 violations

    Note:
        - Optimizes processing by preparing data once for all violation types
        - Processes moves and groups data efficiently
        - Maintains consistent carrier roster across all violation types
        - Used as a faster alternative to individual violation detection
    """
    violations = {
        "8.5.D": [],
        "8.5.F": [],
        "8.5.F NS": [],
        "8.5.F 5th": [],
        "MAX12": [],
        "MAX60": [],
    }

    # Pre-process data once
    data = clock_ring_data.copy()
    data["total_hours"] = pd.to_numeric(data["total"], errors="coerce").fillna(0)
    data["list_status"] = data["list_status"].str.strip().str.lower()

    # Process moves once for all carriers
    moves_result = data.apply(
        lambda x: process_moves_vectorized(x.get("moves", "none"), x["code"]), axis=1
    )
    data = pd.concat([data, moves_result], axis=1)

    # Group data once
    carrier_date_groups = data.groupby(["carrier_name", "rings_date"])

    # Process daily violations
    for (carrier, date), group in carrier_date_groups:
        list_status = group["list_status"].iloc[0]
        total_hours = group["total_hours"].sum()

        # Only process WAL/NL violations for eligible carriers
        if list_status in ["wal", "nl"]:
            # 8.5.D
            off_route_hours = group["off_route_hours"].sum()
            if off_route_hours > 0:
                violations["8.5.D"].append(
                    {
                        "carrier_name": carrier,
                        "date": date,
                        "violation_type": "8.5.D",
                        "remedy_total": off_route_hours,
                        "total_hours": total_hours,
                        "own_route_hours": group["own_route_hours"].sum(),
                        "off_route_hours": off_route_hours,
                        "list_status": list_status,
                    }
                )

            # 8.5.F
            if total_hours > 8:
                violations["8.5.F"].append(
                    {
                        "carrier_name": carrier,
                        "date": date,
                        "violation_type": "8.5.F",
                        "remedy_total": total_hours - 8,
                        "total_hours": total_hours,
                        "list_status": list_status,
                    }
                )

        # Process MAX12 for all carriers
        if total_hours > 12:
            violations["MAX12"].append(
                {
                    "carrier_name": carrier,
                    "date": date,
                    "violation_type": "MAX12",
                    "remedy_total": total_hours - 12,
                    "total_hours": total_hours,
                    "list_status": list_status,
                }
            )

    # Process weekly violations
    weekly_groups = data.groupby("carrier_name")
    for carrier, week_data in weekly_groups:
        list_status = week_data["list_status"].iloc[0]

        # MAX60
        cumulative_hours = week_data.groupby("rings_date")["total_hours"].sum().cumsum()
        if cumulative_hours.max() > 60:
            for date, cum_hours in cumulative_hours[cumulative_hours > 60].items():
                daily_hours = week_data[week_data["rings_date"] == date][
                    "total_hours"
                ].sum()
                violations["MAX60"].append(
                    {
                        "carrier_name": carrier,
                        "date": date,
                        "violation_type": "MAX60",
                        "remedy_total": daily_hours,
                        "total_hours": daily_hours,
                        "cumulative_hours": cum_hours,
                        "list_status": list_status,
                    }
                )

        # 8.5.F 5th day (for WAL/NL only)
        if list_status in ["wal", "nl"]:
            working_days = week_data[week_data["total_hours"] > 0][
                "rings_date"
            ].unique()
            if len(working_days) >= 5:
                fifth_day = sorted(working_days)[4]
                fifth_day_hours = week_data[week_data["rings_date"] == fifth_day][
                    "total_hours"
                ].sum()
                violations["8.5.F 5th"].append(
                    {
                        "carrier_name": carrier,
                        "date": fifth_day,
                        "violation_type": "8.5.F 5th",
                        "remedy_total": fifth_day_hours,
                        "total_hours": fifth_day_hours,
                        "list_status": list_status,
                    }
                )

    # Convert all violations to DataFrames
    return {k: pd.DataFrame(v) if v else pd.DataFrame() for k, v in violations.items()}


@register_violation("8.5.F NS Overtime On a Non-Scheduled Day")
def detect_85f_ns_overtime(data, date_maximized_status=None):
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
        - Not during December

        Remedy:
        - All hours worked beyond 8 on the NS day
        - Unlike regular overtime violations, ALL hours beyond 8 count
          regardless of assignment

        Processing:
        - Analyzes all carriers but only applies violation logic to WAL/NL
        - Identifies NS days through route code analysis
        - Maintains complete carrier roster for reporting consistency
        - Rounds remedy hours to 2 decimal places
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

    # Calculate violations vectorized using conditions directly
    result_df["remedy_total"] = np.where(
        (result_df["list_status"].isin(["wal", "nl"])) & (result_df["is_ns_day"]),
        (result_df["total_hours"] - 8).clip(lower=0).round(2),
        0.0,
    )

    # Set violation types
    result_df["violation_type"] = np.where(
        result_df["remedy_total"] > 0,
        "8.5.F NS Overtime On a Non-Scheduled Day",  # Match the exact string
        "No Violation",
    )

    return result_df[
        [
            "carrier_name",
            "list_status",
            "violation_type",
            "rings_date",
            "remedy_total",
            "total_hours",
        ]
    ].rename(columns={"rings_date": "date"})
