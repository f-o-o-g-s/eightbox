"""Contract violation detection and analysis.

This module implements the core business logic for detecting various types
of contract violations in carrier work schedules, including:

Article 8.5.D Violations:
- Working off bid assignment without proper notification
- Improper assignment of overtime work

Article 8.5.F Violations:
- Non-OTDL carriers working over 10 hours on regular days
- Non-OTDL carriers working over 8 hours on non-scheduled days
- Working overtime on more than 4 of 5 scheduled days

Maximum Hour Violations:
- Exceeding 12-hour daily limit (11.5 for WAL)
- Exceeding 60-hour weekly limit

Features:
- Configurable detection rules
- Remedy calculations
- Multi-day analysis
- List status consideration
- Exception handling for special cases
"""

import json
import os

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


def detect_violations(data, violation_type, date_maximized_status=None):
    """Dispatch violation detection to the appropriate registered function.

    Args:
        data (pd.DataFrame): Carrier work hour data to check for violations
        violation_type (str): Type of violation to detect (e.g., "8.5.F NS", "MAX60")
        date_maximized_status (dict, optional): Date-keyed dict of OTDL maximization status

    Returns:
        pd.DataFrame: Detected violations with calculated remedies

    Note:
        Uses the violation registry populated by @register_violation decorator
        to route detection to the appropriate specialized function.
    """
    if date_maximized_status is None:
        date_maximized_status = {}

    # For violations that don't need excusal data, convert to simple boolean
    if violation_type not in ["8.5.G"]:
        # Convert date_maximized_status values to simple boolean if needed
        if any(isinstance(v, dict) for v in date_maximized_status.values()):
            date_maximized_status = {
                k: v.get("is_maximized", False) if isinstance(v, dict) else v
                for k, v in date_maximized_status.items()
            }

    violation_function = violation_registry[violation_type]
    return violation_function(data, date_maximized_status)


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
        pd.DataFrame: DataFrame with columns:
            - carrier_name
            - list_status
            - date_violation_type columns (e.g. "2024-03-01_8.5.D")
    """
    if not violations:
        # Return empty DataFrame with carrier_name and list_status from original data
        result = pd.DataFrame()
        if (
            not data.empty
            and "carrier_name" in data.columns
            and "list_status" in data.columns
        ):
            result["carrier_name"] = data["carrier_name"]
            result["list_status"] = data["list_status"]
        return result

    # Process all violations at once
    remedy_dfs = []
    for violation_type, violation_data in violations.items():
        if not violation_data.empty:
            # Ensure violation_type is properly set in the data
            violation_data = violation_data.copy()

            # Map full violation types to short types
            violation_type_map = {
                "8.5.D Overtime Off Route": "8.5.D",
                "8.5.F Overtime Over 10 Hours Off Route": "8.5.F",
                "8.5.F NS Overtime On a Non-Scheduled Day": "8.5.F NS",
                "8.5.F 5th More Than 4 Days of Overtime in a Week": "8.5.F 5th",
                "8.5.G OTDL Not Maximized": "8.5.G",
                "MAX12 More Than 12 Hours Worked in a Day": "MAX12",
                "MAX60 More Than 60 Hours Worked in a Week": "MAX60",
            }

            # Use the short type if it's a full type, otherwise use as is
            short_type = violation_type_map.get(violation_type, violation_type)

            # Select only necessary columns
            columns_to_keep = [
                "date",
                "carrier_name",
                "list_status",
                "remedy_total",
            ]
            existing_columns = [
                col for col in columns_to_keep if col in violation_data.columns
            ]
            remedy_df = violation_data[existing_columns].copy()
            remedy_df["violation_type"] = short_type

            remedy_dfs.append(remedy_df)

    if not remedy_dfs:
        # Return empty DataFrame with carrier_name and list_status from original data
        result = pd.DataFrame()
        if (
            not data.empty
            and "carrier_name" in data.columns
            and "list_status" in data.columns
        ):
            result["carrier_name"] = data["carrier_name"]
            result["list_status"] = data["list_status"]
        return result

    # Combine all remedies
    remedy_data = pd.concat(remedy_dfs, ignore_index=True)

    # Ensure we have all carriers from the original data
    if (
        not data.empty
        and "carrier_name" in data.columns
        and "list_status" in data.columns
    ):
        # Get unique carrier data
        unique_carriers = data[["carrier_name", "list_status"]].drop_duplicates()

        # Merge with remedy data to ensure all carriers are included
        remedy_data = pd.merge(
            unique_carriers, remedy_data, on=["carrier_name", "list_status"], how="left"
        )

        # Fill NaN values
        remedy_data["remedy_total"] = remedy_data["remedy_total"].fillna(0)
        remedy_data["date"] = remedy_data["date"].fillna(
            remedy_data["date"].iloc[0] if not remedy_data.empty else ""
        )
        remedy_data["violation_type"] = remedy_data["violation_type"].fillna("")

    # Create pivot table with flattened column names
    pivot_remedy_data = remedy_data.pivot_table(
        index=["carrier_name", "list_status"],
        columns=["date", "violation_type"],
        values="remedy_total",
        aggfunc="sum",
        fill_value=0,
    )

    # Flatten column names to date_violation_type format
    pivot_remedy_data.columns = [
        f"{date}_{vtype}" for date, vtype in pivot_remedy_data.columns
    ]

    # Reset index to make carrier_name and list_status regular columns
    pivot_remedy_data = pivot_remedy_data.reset_index()

    return pivot_remedy_data


@register_violation("8.5.D Overtime Off Route")
def detect_85d_overtime(data, date_maximized_status=None):
    """Detect Article 8.5.D violations for overtime worked off assignment."""
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
                (result_df["total_hours"] - 8).clip(lower=0)
            ),
            0.0
        )
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


def load_exclusion_periods():
    """Load exclusion periods from configuration file.

    Returns:
        tuple: (dict, pd.DatetimeIndex) containing:
            - dict: Raw exclusion periods from config
            - pd.DatetimeIndex: Pre-calculated date range for vectorized comparison
    """
    try:
        config_path = os.path.join(os.path.dirname(__file__), "exclusion_periods.json")
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
        - Not during December exclusion period (varies by year, defined in exclusion_periods.json)

        Remedy is lesser of:
        - Hours worked over 10
        - Hours worked off assignment

        Processing:
        - Analyzes all carriers but only applies violation logic to WAL/NL
        - OTDL and PTF carriers are included in output but marked as "No Violation"
        - Maintains complete carrier roster for reporting consistency
        - December exclusion period is configurable per year
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
    """Detect Article 8.5.F violations for fifth overtime day in a week."""
    # Keep all carriers but only process violations for WAL/NL
    result_df = data.copy()
    
    # Convert numeric columns safely
    result_df["total_hours"] = pd.to_numeric(result_df["total"], errors="coerce").fillna(0)
    result_df["leave_time"] = pd.to_numeric(result_df.get("leave_time", 0), errors="coerce").fillna(0)
    result_df["leave_type"] = result_df["leave_type"].astype(str)
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()
    
    # Calculate daily hours with holiday handling vectorized
    holiday_mask = (result_df["leave_type"].str.lower() == "holiday") & (result_df["leave_time"] == 8.00)
    result_df["daily_hours"] = np.where(
        holiday_mask,
        result_df["total_hours"],
        np.where(
            result_df["leave_time"] <= result_df["total_hours"],
            np.maximum(result_df["total_hours"], result_df["leave_time"]),
            result_df["total_hours"] + result_df["leave_time"]
        )
    )
    
    # Add display indicators
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)
    
    # Convert dates to datetime for comparison
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])
    
    # Create service week groups (Saturday to Friday)
    result_df["service_week"] = result_df["date_dt"].dt.to_period('W-SAT')
    result_df["day_of_week"] = result_df["date_dt"].dt.dayofweek  # Monday=0, Sunday=6
    
    # Load exclusion periods and get pre-calculated date range
    _, exclusion_dates = load_exclusion_periods()
    
    # Vectorized exclusion period check
    result_df["is_excluded"] = result_df["date_dt"].isin(exclusion_dates)
    
    # Process all carriers but only calculate violations for WAL/NL
    base_result = []
    for carrier in result_df["carrier_name"].unique():
        carrier_data = result_df[result_df["carrier_name"] == carrier].sort_values("date_dt")
        list_status = carrier_data["list_status"].iloc[0]
        is_eligible = list_status in ["wal", "nl"]
        
        # Skip if not eligible or in exclusion period
        if not is_eligible or carrier_data["is_excluded"].any():
            for _, day in carrier_data.iterrows():
                base_result.append({
                    "carrier_name": carrier,
                    "date": day["rings_date"],
                    "list_status": day["list_status"],
                    "violation_type": "No Violation (December Exclusion)" if day["is_excluded"] else "No Violation",
                    "remedy_total": 0.0,
                    "total_hours": day["daily_hours"],
                    "display_indicator": day["display_indicator"],
                    "85F_5th_date": ""
                })
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
                base_result.append({
                    "carrier_name": carrier,
                    "date": day["rings_date"],
                    "list_status": day["list_status"],
                    "violation_type": "No Violation",
                    "remedy_total": 0.0,
                    "total_hours": day["daily_hours"],
                    "display_indicator": day["display_indicator"],
                    "85F_5th_date": ""
                })
            continue
        
        # Find potential violation days
        overtime_days = carrier_data[
            (carrier_data["day_of_week"] != 6) &  # Exclude Sundays
            (carrier_data["daily_hours"] > 8)
        ].sort_values("date_dt")
        
        violation_date = None
        if len(overtime_days) >= 5:
            # Get the 5th overtime day in sequence
            violation_date = overtime_days.iloc[4]["rings_date"]
        
        # Add all days for this carrier
        for _, day in carrier_data.iterrows():
            is_violation = day["rings_date"] == violation_date
            base_result.append({
                "carrier_name": carrier,
                "date": day["rings_date"],
                "list_status": day["list_status"],
                "violation_type": "8.5.F 5th More Than 4 Days of Overtime in a Week" if is_violation else "No Violation",
                "remedy_total": round(max(0, day["daily_hours"] - 8), 2) if is_violation else 0.0,
                "total_hours": day["daily_hours"],
                "display_indicator": day["display_indicator"],
                "85F_5th_date": violation_date if is_violation else ""
            })
    
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
        "85F_5th_date"
    ]
    
    # Return DataFrame with columns in the expected order
    return result_df[required_columns]


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

    # Ensure leave_time is numeric
    if "leave_time" in result_df.columns:
        result_df["leave_time"] = pd.to_numeric(
            result_df["leave_time"], errors="coerce"
        ).fillna(0)

    # Set default hour limits based on list status
    status_limits = {"wal": 12.00, "nl": 11.50, "ptf": 11.50, "otdl": 12.00}

    # First ensure hour_limit exists as a column
    if "hour_limit" not in result_df.columns:
        result_df["hour_limit"] = 12.00  # Default value

    # Convert hour_limit to numeric as float64, handling any non-numeric values
    result_df["hour_limit"] = pd.to_numeric(
        result_df["hour_limit"], errors="coerce", downcast=None
    ).astype("float64")

    # Apply status-based defaults where hour_limit is missing
    for status, limit in status_limits.items():
        mask = (result_df["list_status"] == status) & (result_df["hour_limit"].isna())
        result_df.loc[mask, "hour_limit"] = float(limit)

    # Fill any remaining NaN values with default 12.00
    result_df["hour_limit"] = result_df["hour_limit"].fillna(12.00)

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


def generate_display_indicators(data):
    """Generate display indicators for a DataFrame."""
    result_df = data.copy()
    result_df["display_indicator"] = ""

    # Ensure code column exists
    if "code" not in result_df.columns:
        result_df["code"] = ""

    # Check for NS day in code (case insensitive)
    ns_mask = (
        result_df["code"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.contains("ns day", na=False)
    )
    result_df.loc[ns_mask, "display_indicator"] += "(NS day) "

    # Check for NS protection (case insensitive)
    ns_protect_mask = (
        result_df["code"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.contains("ns protect", na=False)
    )
    result_df.loc[ns_protect_mask, "display_indicator"] += "(NS protect) "

    # Add leave type indicators if leave_type column exists
    if "leave_type" in result_df.columns:
        # Convert leave_type to string, strip whitespace, and convert to lowercase
        leave_types = result_df["leave_type"].astype(str).str.strip().str.lower()
        leave_time = pd.to_numeric(result_df["leave_time"], errors="coerce").fillna(0)

        leave_type_map = {
            "sick": "(sick)",
            "annual": "(annual)",
            "holiday": "(holiday)",
            "guaranteed": "(guaranteed)",
        }

        for leave_type, indicator in leave_type_map.items():
            # Check if leave type matches and has positive leave time
            leave_mask = (leave_types == leave_type) & (leave_time > 0)
            result_df.loc[leave_mask, "display_indicator"] += f"{indicator} "

        # Special handling for guaranteed time (might be in code column)
        guaranteed_mask = (
            result_df["code"]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains("guaranteed", na=False)
        )
        result_df.loc[guaranteed_mask, "display_indicator"] += "(guaranteed) "

    # Clean up any double spaces and strip
    result_df["display_indicator"] = result_df["display_indicator"].str.strip()

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
        - Not during December exclusion period (varies by year, defined in exclusion_periods.json)

        Remedy:
        - All hours worked beyond 8 on the NS day
        - Unlike regular overtime violations, ALL hours beyond 8 count
          regardless of assignment

        Processing:
        - Analyzes all carriers but only applies violation logic to WAL/NL
        - Identifies NS days through route code analysis
        - Maintains complete carrier roster for reporting consistency
        - December exclusion period is configurable per year
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


@register_violation("8.5.G")
def detect_85g_violations(data, date_maximized_status=None):
    """Detect Article 8.5.G violations for OTDL carriers not maximized."""
    
    # First prepare the basic data
    result_df = prepare_data_for_violations(data)
    
    # Then add display indicators specifically for 8.5.G processing
    result_df = generate_display_indicators(result_df)
    
    # Convert dates to datetime for vectorized operations
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])
    result_df["day_of_week"] = result_df["date_dt"].dt.strftime("%A")
    
    # Vectorized checks for auto-excusal indicators
    auto_excusal_indicators = ["(sick)", "(NS protect)", "(holiday)", "(guaranteed)", "(annual)"]
    result_df["is_auto_excused"] = result_df["display_indicator"].apply(
        lambda x: any(indicator in str(x) for indicator in auto_excusal_indicators)
    )
    result_df["is_sunday"] = result_df["day_of_week"].astype(str) == "Sunday"
    
    # Convert numeric columns safely
    result_df["total_hours"] = pd.to_numeric(result_df["total_hours"], errors="coerce").fillna(0)
    result_df["hour_limit"] = pd.to_numeric(result_df["hour_limit"], errors="coerce").fillna(12.00)
    
    # Create maximized status DataFrame for vectorized lookup
    max_status_df = pd.DataFrame()
    if date_maximized_status:
        max_status_records = []
        for date_str, status in date_maximized_status.items():
            if isinstance(status, dict):
                is_maximized = status.get("is_maximized", False)
                excused_carriers = set(str(c) for c in status.get("excused_carriers", []))
                carrier_excusals = {
                    str(k): v 
                    for k, v in status.items() 
                    if k not in ["is_maximized", "excused_carriers"]
                }
                max_status_records.append({
                    "date": pd.to_datetime(date_str),
                    "is_maximized": is_maximized,
                    "excused_carriers": excused_carriers,
                    "carrier_excusals": carrier_excusals
                })
            else:
                max_status_records.append({
                    "date": pd.to_datetime(date_str),
                    "is_maximized": bool(status),
                    "excused_carriers": set(),
                    "carrier_excusals": {}
                })
        max_status_df = pd.DataFrame(max_status_records)
    
    # Merge maximized status with result_df
    if not max_status_df.empty:
        result_df = pd.merge(
            result_df,
            max_status_df,
            left_on="date_dt",
            right_on="date",
            how="left"
        )
    else:
        result_df["is_maximized"] = False
        result_df["excused_carriers"] = None
        result_df["carrier_excusals"] = None
    
    # Vectorized check for manually excused carriers
    def check_manual_excusal(row):
        if pd.isna(row["excused_carriers"]) and pd.isna(row["carrier_excusals"]):
            return False
        carrier_str = str(row["carrier_name"])
        return (
            carrier_str in (row["excused_carriers"] or set()) or
            (row["carrier_excusals"] or {}).get(carrier_str, False)
        )
    
    result_df["is_manually_excused"] = result_df.apply(check_manual_excusal, axis=1)
    
    # Process each date group separately to match original implementation
    final_results = []
    for date, day_data in result_df.groupby("date_dt"):
        date_str = date.strftime("%Y-%m-%d")
        is_maximized = day_data["is_maximized"].iloc[0]
        
        if is_maximized:
            # Handle maximized case
            for _, carrier_data in day_data.iterrows():
                violation_type = (
                    "No Violation (Auto Excused)"
                    if carrier_data["is_auto_excused"] or carrier_data["is_sunday"]
                    else "No Violation (Manually Excused)"
                    if carrier_data["is_manually_excused"]
                    else "No Violation (Maximized)"
                    if carrier_data["total_hours"] >= carrier_data["hour_limit"]
                    else "No Violation"
                )
                
                final_results.append({
                    "carrier_name": carrier_data["carrier_name"],
                    "date": date_str,
                    "violation_type": violation_type,
                    "remedy_total": 0.0,
                    "total_hours": carrier_data["total_hours"],
                    "hour_limit": carrier_data["hour_limit"],
                    "list_status": carrier_data["list_status"],
                    "trigger_carrier": "",
                    "trigger_hours": 0,
                    "off_route_hours": 0,
                    "display_indicator": carrier_data["display_indicator"]
                })
            continue
        
        # Find WAL/NL carriers working overtime
        wal_nl_overtime = day_data[
            (day_data["list_status"].isin(["wal", "nl"])) & 
            (day_data["total_hours"] > 8)
        ]
        
        if not wal_nl_overtime.empty:
            # Get trigger carrier info
            trigger_carrier = wal_nl_overtime.loc[wal_nl_overtime["total_hours"].idxmax()]
            
            # Process OTDL carriers
            otdl_carriers = day_data[day_data["list_status"] == "otdl"]
            for _, otdl in otdl_carriers.iterrows():
                # Get display indicator
                display_indicators = str(otdl["display_indicator"]).strip()
                
                # Check for automatic excusal conditions
                is_auto_excused = any(
                    indicator in display_indicators
                    for indicator in auto_excusal_indicators
                )
                
                violation_type = (
                    "No Violation (Auto Excused)"
                    if is_auto_excused or otdl["is_sunday"]
                    else "No Violation (Maximized)"
                    if otdl["total_hours"] >= otdl["hour_limit"]
                    else "No Violation (Manually Excused)"
                    if otdl["is_manually_excused"]
                    else "8.5.G OTDL Not Maximized"
                )
                
                remedy_total = (
                    max(0, round(otdl["hour_limit"] - otdl["total_hours"], 2))
                    if violation_type == "8.5.G OTDL Not Maximized"
                    else 0.0
                )
                
                final_results.append({
                    "carrier_name": otdl["carrier_name"],
                    "date": date_str,
                    "violation_type": violation_type,
                    "remedy_total": remedy_total,
                    "total_hours": otdl["total_hours"],
                    "hour_limit": otdl["hour_limit"],
                    "list_status": "otdl",
                    "trigger_carrier": str(trigger_carrier["carrier_name"]),
                    "trigger_hours": float(trigger_carrier["total_hours"]),
                    "off_route_hours": float(trigger_carrier.get("off_route_hours", 0)),
                    "display_indicator": otdl["display_indicator"]
                })
        
        # Add remaining carriers
        processed_carriers = {r["carrier_name"] for r in final_results if r["date"] == date_str}
        remaining_carriers = day_data[~day_data["carrier_name"].isin(processed_carriers)]
        
        for _, carrier_data in remaining_carriers.iterrows():
            # For non-OTDL carriers, always use "No Violation (Non OTDL)"
            violation_type = (
                "No Violation (Non OTDL)"
                if carrier_data["list_status"] != "otdl"
                else "No Violation (Auto Excused)"
                if carrier_data["is_auto_excused"] or carrier_data["is_sunday"]
                else "No Violation (Manually Excused)"
                if carrier_data["is_manually_excused"]
                else "No Violation (Maximized)"
                if carrier_data["total_hours"] >= carrier_data["hour_limit"]
                else "No Violation"
            )
            
            final_results.append({
                "carrier_name": carrier_data["carrier_name"],
                "date": date_str,
                "violation_type": violation_type,
                "remedy_total": 0.0,
                "total_hours": carrier_data["total_hours"],
                "hour_limit": carrier_data["hour_limit"],
                "list_status": carrier_data["list_status"],
                "trigger_carrier": "",
                "trigger_hours": 0,
                "off_route_hours": 0,
                "display_indicator": carrier_data["display_indicator"]
            })
    
    return pd.DataFrame(final_results).sort_values("carrier_name", ascending=True).reset_index(drop=True)