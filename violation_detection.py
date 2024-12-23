"""Contract violation detection and analysis.

This module serves as the central dispatcher and coordinator for detecting
various types of contract violations in carrier work schedules. After refactoring,
the specific violation detection logic has been moved to dedicated modules in
the violation_formulas/ directory.

Core Responsibilities:
- Violation type registration and dispatch
- Move processing and analysis
- Remedy hour aggregation
- Data preparation and standardization
- Display indicator generation

Violation Types (implemented in violation_formulas/):
- Article 8.5.D (article_85d.py):
  Working off bid assignment without proper notification

- Article 8.5.F (article_85f.py):
  Non-OTDL carriers working over 10 hours on regular days

- Article 8.5.F NS (article_85f_ns.py):
  Non-OTDL carriers working over 8 hours on non-scheduled days

- Article 8.5.F 5th (article_85f_5th.py):
  Working overtime on more than 4 of 5 scheduled days

- Article 8.5.G (article_85g.py):
  OTDL carriers not maximized while others work overtime

- Maximum Hours (max12.py, max60.py):
  Daily (12-hour) and weekly (60-hour) limits

Features:
- Centralized violation registration system
- Vectorized move processing
- Flexible remedy aggregation
- Standardized data preparation
- Configurable display indicators

Note:
The actual violation detection logic for each type has been moved to
separate modules in the violation_formulas/ directory for better
maintainability and testing. This module now focuses on coordination
and shared utilities."""

from typing import (
    Callable,
    Dict,
    Optional,
)

import pandas as pd

from violation_formulas.article_85d import detect_85d_violations
from violation_formulas.article_85f import detect_85f_violations
from violation_formulas.article_85f_5th import detect_85f_5th_violations
from violation_formulas.article_85f_ns import detect_85f_ns_violations
from violation_formulas.article_85g import detect_85g_violations
from violation_formulas.max12 import detect_MAX_12
from violation_formulas.max60 import detect_MAX_60

# Type alias for violation detection function
ViolationFunc = Callable[[pd.DataFrame, Optional[dict]], pd.DataFrame]

# Registry for violation detection functions
registered_violations: Dict[str, ViolationFunc] = {}
violation_registry: Dict[str, ViolationFunc] = {}


def register_violation(violation_type: str) -> Callable[[ViolationFunc], ViolationFunc]:
    """Register a violation detection function for a specific violation type."""

    def decorator(func: ViolationFunc) -> ViolationFunc:
        violation_registry[violation_type] = func
        return func

    return decorator


# Register the violation detection functions
register_violation("8.5.D Overtime Off Route")(detect_85d_violations)
register_violation("8.5.F Overtime Over 10 Hours Off Route")(detect_85f_violations)
register_violation("8.5.F NS Overtime On a Non-Scheduled Day")(detect_85f_ns_violations)
register_violation("8.5.F 5th More Than 4 Days of Overtime in a Week")(
    detect_85f_5th_violations
)
register_violation("8.5.G")(detect_85g_violations)
register_violation("MAX12 More Than 12 Hours Worked in a Day")(detect_MAX_12)
register_violation("MAX60 More Than 60 Hours Worked in a Week")(detect_MAX_60)


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
    if violation_type not in ["8.5.G OTDL Not Maximized"]:
        # Convert date_maximized_status values to simple boolean if needed
        if any(isinstance(v, dict) for v in date_maximized_status.values()):
            date_maximized_status = {
                k: v.get("is_maximized", False) if isinstance(v, dict) else v
                for k, v in date_maximized_status.items()
            }

    violation_function = violation_registry[violation_type]
    return violation_function(data, date_maximized_status)


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
