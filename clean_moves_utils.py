"""Utilities for detecting and cleaning invalid moves data.

This module provides functionality to:
1. Detect moves with invalid route numbers (0000)
2. Validate route numbers against the carriers table
3. Clean and format moves data
"""

import re
import sqlite3
from typing import (
    Dict,
    List,
    Set,
    Tuple,
)

import pandas as pd


def get_valid_routes(db_path: str) -> Set[str]:
    """Get set of valid route numbers from carriers table.

    Args:
        db_path: Path to the mandates.sqlite database

    Returns:
        Set of valid route numbers from route_s column
    """
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT DISTINCT route_s
                FROM carriers
                WHERE route_s IS NOT NULL AND route_s != ''
            """
            df = pd.read_sql_query(query, conn)
            # Convert route_s to 4-digit format and remove any invalid formats
            routes = set()
            for route in df["route_s"].dropna():
                try:
                    # Convert to 4-digit format
                    route_num = int(route)
                    if 0 < route_num < 10000:  # Valid range
                        routes.add(f"{route_num:04d}")
                except ValueError:
                    continue
            return routes
    except Exception as e:
        print(f"Error getting valid routes: {e}")
        return set()


def format_moves_breakdown(moves_str):
    """Format moves into a readable breakdown with route and hours.

    Args:
        moves_str: String of moves in format "start1,end1,route1,start2,end2,route2,..."

    Returns:
        String with format "route1 (X.XX hrs), route2 (Y.YY hrs)"
    """
    if not moves_str:
        return ""

    moves = parse_moves_entry(moves_str)
    if not moves:
        return ""

    # Format each move
    breakdowns = []
    for start, end, route in moves:
        # Calculate hours in centesimal format
        hours = end - start
        if hours < 0:  # Handle moves crossing midnight
            hours += 24
        breakdowns.append(f"rt{route} ({hours:.2f} hrs)")

    return ", ".join(breakdowns)


def detect_invalid_moves(moves_data: pd.DataFrame, db_path: str) -> pd.DataFrame:
    """Detect moves entries with invalid route numbers or excessive hours.

    Args:
        moves_data: DataFrame containing moves data
        db_path: Path to the mandates.sqlite database

    Returns:
        DataFrame containing entries with:
        - "0000" routes
        - Non-standard route numbers (not 4 digits or 5 digits starting with 0)
        - Individual moves > 4.25 hours
        - Combined moves > 4.25 hours for the day
    """

    def check_moves_validity(moves_str: str) -> Tuple[bool, str, float]:
        """Check moves string for invalid routes and excessive hours.

        Returns:
            Tuple of (has_issues, reason, total_moves_hours)
        """
        if not isinstance(moves_str, str) or moves_str.strip().lower() in [
            "none",
            "",
            "no moves",
        ]:
            return False, "", 0.0

        try:
            # Split moves into components
            parts = [x.strip() for x in moves_str.split(",")]
            total_moves_hours = 0.0
            has_invalid_route = False
            excessive_single_move = False

            # Process in groups of 3 (start, end, route)
            for i in range(0, len(parts), 3):
                start = float(parts[i])
                end = float(parts[i + 1])
                route = parts[i + 2]

                # Calculate hours for this move
                hours = end - start
                total_moves_hours += hours

                # Check for invalid route format
                if route == "0000" or not (
                    (len(route) == 4 and route.isdigit())
                    or (  # Regular route
                        len(route) == 5 and route[0] == "0" and route.isdigit()
                    )  # Collection route
                ):
                    has_invalid_route = True

                # Check for excessive single move
                if hours > 4.25:
                    excessive_single_move = True

            # Determine reason for flagging
            reason = []
            if has_invalid_route:
                reason.append("Invalid route(s)")
            if excessive_single_move:
                reason.append("Single move > 4.25 hrs")
            if total_moves_hours > 4.25:
                reason.append("Total moves > 4.25 hrs")

            return bool(reason), ", ".join(reason), total_moves_hours

        except Exception:
            return False, "Error parsing moves", 0.0

    # Apply validity check to moves data
    invalid_moves = []

    for _, row in moves_data.iterrows():
        has_issues, reason, total_hours = check_moves_validity(row["moves"])
        if has_issues:
            invalid_move = row.copy()
            invalid_move["Issue"] = reason
            invalid_move["Total Moves Hours"] = total_hours
            invalid_moves.append(invalid_move)

    if not invalid_moves:
        return pd.DataFrame()

    result = pd.DataFrame(invalid_moves)

    # Add human-readable breakdown column
    result["Moves Breakdown"] = result["moves"].apply(format_moves_breakdown)

    return result


def parse_moves_entry(moves_str: str) -> List[Tuple[float, float, str]]:
    """Parse a moves string into a list of (start, end, route) tuples.

    Args:
        moves_str: Comma-separated moves string

    Returns:
        List of (start_time, end_time, route) tuples
    """
    if not isinstance(moves_str, str) or moves_str.strip().lower() in [
        "none",
        "",
        "no moves",
    ]:
        return []

    try:
        parts = [x.strip() for x in moves_str.split(",")]
        moves = []

        # Process in groups of 3 (start, end, route)
        for i in range(0, len(parts), 3):
            start = float(parts[i])
            end = float(parts[i + 1])
            route = parts[i + 2]
            moves.append((start, end, route))

        return moves
    except Exception:
        return []


def validate_route_number(route: str, valid_routes: Set[str]) -> bool:
    """Validate a route number.

    Args:
        route: Route number to validate
        valid_routes: Set of valid route numbers

    Returns:
        True if route is valid, False otherwise
    """
    if not route or route == "0000":
        return False

    # Must be 4 or 5 digits
    if not (len(route) in [4, 5] and route.isdigit()):
        return False

    # Collection routes start with '0' and are 5 digits
    if len(route) == 5 and route[0] == "0":
        return True  # Allow any 5-digit route starting with 0

    # Allow 4-digit routes regardless of leading zero
    if len(route) == 4:
        return True

    return False


def validate_move_times(start: float, end: float) -> bool:
    """Validate move start and end times in centesimal format.

    Args:
        start: Start time in HH.HH format (where HH is hours and HH is hundredths)
        end: End time in HH.HH format

    Returns:
        True if times are valid, False otherwise
    """
    try:
        # Split into hours and hundredths
        start_hour = int(start)
        start_hundredths = int((start % 1) * 100)
        end_hour = int(end)
        end_hundredths = int((end % 1) * 100)

        # Validate ranges
        if not (0 <= start_hour <= 24 and 0 <= end_hour <= 24):
            return False

        if not (0 <= start_hundredths <= 99 and 0 <= end_hundredths <= 99):
            return False

        # Special case: 24.00 is valid, but 24.01-24.99 are not
        if start_hour == 24 and start_hundredths > 0:
            return False
        if end_hour == 24 and end_hundredths > 0:
            return False

        # Convert to total hundredths for comparison
        start_total = start_hour * 100 + start_hundredths
        end_total = end_hour * 100 + end_hundredths

        # Handle crossing midnight
        if start_hour > end_hour:
            end_total += 2400  # Add 24 hours worth of hundredths

        return end_total > start_total

    except Exception:
        return False


def update_moves_in_database(
    db_path: str, cleaned_moves: Dict[Tuple[str, str], str]
) -> bool:
    """Update moves in the database with cleaned values.

    Args:
        db_path: Path to the mandates.sqlite database
        cleaned_moves: Dictionary mapping (carrier_name, date) to cleaned moves string

    Returns:
        True if update successful, False otherwise
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Update each cleaned move
            for (carrier_name, date), moves in cleaned_moves.items():
                cursor.execute(
                    """
                    UPDATE rings3
                    SET moves = ?
                    WHERE carrier_name = ? AND DATE(rings_date) = ?
                """,
                    (moves, carrier_name, date),
                )

            conn.commit()
            return True

    except Exception as e:
        print(f"Error updating moves in database: {e}")
        return False


def validate_time_input(time_str):
    """Validate time input in postal centesimal format (HH.HH)."""
    if not time_str:
        return True

    try:
        # Remove any spaces
        time_str = time_str.strip()

        # Check if the input matches the format HH.HH
        if not re.match(r"^\d{1,2}\.\d{2}$", time_str):
            return False

        hours, centesimal = map(float, time_str.split("."))

        # Validate hours (0-24) and centesimal part (0-99)
        if not (0 <= hours <= 24 and 0 <= centesimal <= 99):
            return False

        # Special case: 24.00 is valid, but 24.01 is not
        if hours == 24 and centesimal > 0:
            return False

        return True

    except (ValueError, AttributeError):
        return False
