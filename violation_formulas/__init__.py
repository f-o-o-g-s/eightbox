"""Violation formula package.

This package contains modules for detecting and calculating remedies for
various contract violations:

- Article 8.5.D: Working off bid assignment without proper notification
- Article 8.5.F: Non-OTDL carriers working overtime
- Article 8.5.F NS: Non-OTDL carriers working overtime on non-scheduled days
- Article 8.5.F 5th: Non-OTDL carriers working overtime on more than 4 days
- Article 8.5.G: OTDL carriers not maximized
- MAX12: Exceeding 12-hour daily limit
- MAX60: Exceeding 60-hour weekly limit
"""

from .article_85d import detect_85d_violations
from .article_85f import detect_85f_violations
from .article_85f_5th import detect_85f_5th_violations
from .article_85f_ns import detect_85f_ns_violations
from .article_85g import detect_85g_violations
from .max12 import detect_MAX_12
from .max60 import detect_MAX_60

__all__ = [
    "detect_85d_violations",
    "detect_85f_violations",
    "detect_85f_ns_violations",
    "detect_85f_5th_violations",
    "detect_85g_violations",
    "detect_MAX_12",
    "detect_MAX_60",
]
