"""Database models and data types.

This module contains the data classes and types used for database operations.
"""

from dataclasses import dataclass
from datetime import date
from typing import (
    Any,
    Dict,
    Optional,
)


@dataclass
class ClockRingQueryParams:
    """Parameters for clock ring data queries.

    Attributes:
        start_date: Start date for the query
        end_date: End date for the query
        db_path: Path to the database
        carrier_list_path: Optional path to carrier list JSON file
    """

    start_date: date
    end_date: date
    db_path: str
    carrier_list_path: Optional[str] = "carrier_list.json"


@dataclass
class DatabaseError:
    """Represents a database operation error.

    Attributes:
        message: Human-readable error message
        error_type: Type of error (e.g., PATH_ERROR, QUERY_ERROR)
        details: Optional dictionary with additional error details
    """

    message: str
    error_type: str
    details: Optional[Dict[str, Any]] = None
