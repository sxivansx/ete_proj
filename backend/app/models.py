"""Domain model for a parsed course attainment sheet.

These types are deliberately dumb data holders. All math lives in
``calculator.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

#: Broad column kind in the CIE+SEE layout.
ColumnKind = Literal["question", "tot", "test", "aat", "final", "see"]


@dataclass(frozen=True)
class Column:
    """One column from the CIE+SEE sheet."""

    index: int                       # 1-indexed Excel column
    kind: ColumnKind
    label: str                       # "Q1", "TOT", "AAT (ASSGN)", ...
    max_marks: float                 # from row 7
    co_tags: tuple[int, ...]         # COs this column contributes to (may be empty)
    ia_index: int | None = None      # 1-based IA number for question/tot cols, else None


@dataclass(frozen=True)
class StudentRow:
    sl_no: int
    usn: str
    #: column_index -> mark. ``None`` means the cell is blank (not attempted).
    #: A ``str`` (e.g. ``"NE"`` for "Not Eligible") means the cell is present
    #: but non-numeric — Excel's ``COUNTIF("<>")`` treats such cells as
    #: attempted, so we preserve them and let the calculator decide.
    marks: dict[int, float | str | None]


@dataclass(frozen=True)
class CourseSheet:
    """Everything the calculator needs from one workbook."""

    path: str
    course_name: str
    columns: tuple[Column, ...]
    students: tuple[StudentRow, ...]
    co_numbers: tuple[int, ...] = field(default_factory=tuple)

    # ---- convenience lookups -------------------------------------------------

    def columns_by_kind(self, *kinds: ColumnKind) -> tuple[Column, ...]:
        return tuple(c for c in self.columns if c.kind in kinds)

    def ia_question_columns(self, ia_index: int) -> tuple[Column, ...]:
        return tuple(
            c for c in self.columns
            if c.kind == "question" and c.ia_index == ia_index
        )

    def ia_indices(self) -> tuple[int, ...]:
        seen: list[int] = []
        for c in self.columns:
            if c.ia_index is not None and c.ia_index not in seen:
                seen.append(c.ia_index)
        return tuple(seen)

    def column(self, kind: ColumnKind) -> Column | None:
        for c in self.columns:
            if c.kind == kind:
                return c
        return None
