"""Defines the ViolationType enum used throughout the application.

This module provides a centralized enum for all violation types supported
by the application, ensuring consistent type checking and preventing string
literal errors in violation handling code.
"""

from enum import Enum


class ViolationType(Enum):
    """Enum for different types of violations tracked in the system."""

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
