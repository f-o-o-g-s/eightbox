"""Violation tab implementations."""

from .violation_85d_tab import Violation85dTab
from .violation_85f_tab import Violation85fTab
from .violation_85f_5th_tab import Violation85f5thTab
from .violation_85f_ns_tab import Violation85fNsTab
from .violation_85g_tab import Violation85gTab
from .violation_max12_tab import ViolationMax12Tab
from .violation_max60_tab import ViolationMax60Tab
from .violations_summary_tab import ViolationRemediesTab

__all__ = [
    'Violation85dTab',
    'Violation85fTab',
    'Violation85f5thTab',
    'Violation85fNsTab',
    'Violation85gTab',
    'ViolationMax12Tab',
    'ViolationMax60Tab',
    'ViolationRemediesTab',
]
