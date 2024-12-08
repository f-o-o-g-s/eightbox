"""Defines the ViolationType enum used throughout the application.

This module provides a centralized enum for all violation types supported
by the application, ensuring consistent type checking and preventing string
literal errors in violation handling code.
"""

from enum import Enum


class ViolationType(Enum):
    """Enumeration of carrier overtime violation categories.

    Each value represents a specific type of overtime violation,
    with distinct rules for:
    - When the violation occurs
    - How remedy hours are calculated
    - Which carriers are affected
    - Display formatting requirements

    Attributes:
        EIGHT_FIVE_D: Article 8.5.D - Overtime off assignment
        EIGHT_FIVE_F: Article 8.5.F - Over 10 hours (regular day)
        EIGHT_FIVE_F_NS: Article 8.5.F - Over 8 hours (non-scheduled day)
        EIGHT_FIVE_F_5TH: Article 8.5.F - 5th overtime day
        MAX_12: Maximum 12-hour rule (11.5 for non-OTDL)
        MAX_60: Maximum 60-hour weekly limit
        VIOLATION_REMEDIES: Combined violation summary view
    """

    EIGHT_FIVE_D = "85d"
    EIGHT_FIVE_F = "85f"
    EIGHT_FIVE_F_NS = "85f_ns"
    EIGHT_FIVE_F_5TH = "85f_5th"
    MAX_12 = "max12"
    MAX_60 = "max60"
    VIOLATION_REMEDIES = "ViolationRemedies"

    def __str__(self) -> str:
        """Return the value of the enum for string representation."""
        return self.value
