"""
Domain Value Objects: Triage Priority and Modality types (Zero dependencies).
"""
from enum import Enum


class Modality(str, Enum):
    CT = "CT"
    MR = "MR"
    XR = "XR"
    US = "US"
    PET = "PET"
    NM = "NM"


class TriagePriority(str, Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"  # Critical immediate life-threat (e.g. Hemorrhage, Pneumothorax)

    @property
    def max_turnaround_minutes(self) -> int:
        match self:
            case TriagePriority.STAT:
                return 15
            case TriagePriority.URGENT:
                return 60
            case TriagePriority.ROUTINE:
                return 240
