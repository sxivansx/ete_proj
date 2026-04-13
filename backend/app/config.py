"""Configuration constants for the CO Attainment calculator.

Anything that a user might want to tune lives here. The sheet-layout
constants are derived from the faculty's existing template — if the template
changes, update this module and the parser follows.
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Weighting / thresholds
# ---------------------------------------------------------------------------

#: Fraction of a question's max marks that counts as "passing" for attainment.
DEFAULT_PASS_FRACTION: float = 0.6

#: CIE weight in Direct CO attainment (CIE * w + SEE * (1 - w)).
DEFAULT_CIE_WEIGHT: float = 0.6

#: Direct weight in Final CO attainment (Direct * w + Indirect * (1 - w)).
DEFAULT_DIRECT_WEIGHT: float = 0.9


# ---------------------------------------------------------------------------
# Sheet layout (CIE+SEE sheet of the faculty template)
# ---------------------------------------------------------------------------

SHEET_CIE_SEE: str = "CIE+SEE"

#: 1-indexed row numbers in the CIE+SEE sheet.
ROW_SECTION_HEADER: int = 4   # "INTERNAL ASSESMENT-1" etc. and special column titles
ROW_QUESTION_LABEL: int = 5   # "Q1", "Q2", ..., "TEST", "AAT (ASSGN)", "FINAL", "SEE"
ROW_CO_TAG: int = 6           # CO number(s) per column
ROW_MAX_MARKS: int = 7        # max marks per column
ROW_THRESHOLD: int = 8        # =0.6 * max_marks (we recompute, don't trust)
ROW_STUDENT_START: int = 10   # first student row
COL_SL_NO: int = 1
COL_USN: int = 2
COL_FIRST_QUESTION: int = 3   # first question column (C)

#: Labels in row 5 that identify the special (non-IA) columns.
LABEL_TEST: str = "TEST"
LABEL_AAT: str = "AAT (ASSGN)"
LABEL_FINAL: str = "FINAL"
LABEL_SEE: str = "SEE"
LABEL_TOT: str = "TOT"


@dataclass(frozen=True)
class CalcConfig:
    """Runtime knobs the caller can override."""

    pass_fraction: float = DEFAULT_PASS_FRACTION
    cie_weight: float = DEFAULT_CIE_WEIGHT
    direct_weight: float = DEFAULT_DIRECT_WEIGHT

    def __post_init__(self) -> None:
        for name, value in (
            ("pass_fraction", self.pass_fraction),
            ("cie_weight", self.cie_weight),
            ("direct_weight", self.direct_weight),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")
