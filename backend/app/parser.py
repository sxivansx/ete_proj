"""Read a faculty CIE+SEE workbook into a :class:`CourseSheet`.

The parser is intentionally tolerant — CO tags can be ints, comma-lists, or
phrases like ``"CO 1 2 3 4"``; blank student cells mean "not attempted".
"""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell

from . import config
from .models import Column, ColumnKind, CourseSheet, StudentRow


_CO_NUMBER_RE = re.compile(r"\d+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_co_tags(raw: object) -> tuple[int, ...]:
    """Extract the integer CO numbers from a row-6 tag cell.

    Handles:
      - ``None``                   -> ``()``
      - int ``2``                  -> ``(2,)``
      - str ``"2,3"`` / ``"2 3"``  -> ``(2, 3)``
      - str ``"CO 1 2 3 4"``       -> ``(1, 2, 3, 4)``
    """
    if raw is None:
        return ()
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return (int(raw),)
    if isinstance(raw, str):
        nums = [int(m.group()) for m in _CO_NUMBER_RE.finditer(raw)]
        # In strings like "CO 1 2 3 4" the leading "CO" contributes no digits,
        # so this works without special casing.
        return tuple(nums)
    return ()


def _parse_mark(cell: Cell) -> float | str | None:
    """Return ``None`` for a truly blank cell, ``float`` for numeric marks,
    or the raw ``str`` (e.g. ``"NE"``) for non-numeric text cells.

    Matching Excel semantics: ``COUNTIF(range, "<>")`` counts any non-blank
    cell including text, so we must distinguish ``None`` from ``"NE"``.
    """
    value = cell.value
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return value.strip()  # e.g. "NE" — present but not numeric
    return None


_SPECIAL_LABELS = {
    config.LABEL_TEST: "test",
    config.LABEL_AAT: "aat",
    config.LABEL_FINAL: "final",
    config.LABEL_SEE: "see",
}


def _classify_column(
    label: str | None,
    max_marks: float,
    co_tags: tuple[int, ...],
    current_question_label: str | None,
    ia_counter: dict[str, int],
) -> tuple[ColumnKind | None, int | None, str | None]:
    """Return ``(kind, ia_index, resolved_label)`` for one column.

    Layout quirk: each CIE question spans **two** sub-columns. Only the first
    has a row-5 label (``"Q1"``) — the second is unlabeled but carries its
    own CO tag and max marks. We treat both as separate "question" columns,
    with the unlabeled one inheriting the label (``"Q1"``) of its parent.

    Returns ``(None, None, None)`` for columns that should be skipped.
    """
    if label in _SPECIAL_LABELS:
        return _SPECIAL_LABELS[label], None, label
    if label == config.LABEL_TOT:
        ia = ia_counter["current"]
        ia_counter["current"] += 1  # next block of Qs belongs to the next IA
        return "tot", ia, label
    # A labelled question column ("Q1", "Q2", ...).
    if label is not None:
        return "question", ia_counter["current"], label
    # An unlabeled sub-column — treat as a question sub-part **only if** it
    # has a max mark and a CO tag (otherwise it's just trailing empty space).
    if max_marks > 0 and co_tags:
        return "question", ia_counter["current"], current_question_label
    return None, None, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_course_sheet(path: str | Path) -> CourseSheet:
    """Parse the CIE+SEE sheet of *path* into a :class:`CourseSheet`."""
    path = Path(path)
    wb = load_workbook(path, data_only=True, read_only=False)
    if config.SHEET_CIE_SEE not in wb.sheetnames:
        raise ValueError(
            f"Workbook {path.name!r} is missing required sheet "
            f"{config.SHEET_CIE_SEE!r}; found {wb.sheetnames}"
        )
    ws = wb[config.SHEET_CIE_SEE]

    course_name = ""
    # Row 2 col B in the template holds the subject name.
    sub_label = ws.cell(row=2, column=1).value
    sub_value = ws.cell(row=2, column=2).value
    if isinstance(sub_label, str) and sub_label.strip().upper() == "SUB" and sub_value:
        course_name = str(sub_value).strip()

    # --- Columns --------------------------------------------------------------
    columns: list[Column] = []
    co_numbers_seen: set[int] = set()
    ia_counter = {"current": 1}
    last_question_label: str | None = None

    for col_idx in range(config.COL_FIRST_QUESTION, ws.max_column + 1):
        label_cell = ws.cell(row=config.ROW_QUESTION_LABEL, column=col_idx).value
        label = (
            str(label_cell).strip()
            if label_cell is not None and str(label_cell).strip()
            else None
        )

        max_marks_raw = ws.cell(row=config.ROW_MAX_MARKS, column=col_idx).value
        try:
            max_marks = float(max_marks_raw) if max_marks_raw is not None else 0.0
        except (TypeError, ValueError):
            max_marks = 0.0

        co_tags = _parse_co_tags(ws.cell(row=config.ROW_CO_TAG, column=col_idx).value)

        kind, ia_index, resolved_label = _classify_column(
            label, max_marks, co_tags, last_question_label, ia_counter,
        )
        if kind is None:
            continue
        if kind == "question":
            if label is not None:
                last_question_label = label

        co_numbers_seen.update(co_tags)
        columns.append(Column(
            index=col_idx,
            kind=kind,
            label=resolved_label or "",
            max_marks=max_marks,
            co_tags=co_tags,
            ia_index=ia_index,
        ))

    # --- Students -------------------------------------------------------------
    # Student rows have an int in column A (Sl.No). As soon as column A stops
    # being an int we've hit the summary block ("count >60%", CO mapping
    # tables, etc.) and must stop — otherwise we'd treat summary rows as
    # students.
    students: list[StudentRow] = []
    for row in range(config.ROW_STUDENT_START, ws.max_row + 1):
        sl_no_cell = ws.cell(row=row, column=config.COL_SL_NO).value
        usn_cell = ws.cell(row=row, column=config.COL_USN).value
        if not isinstance(sl_no_cell, (int, float)) or isinstance(sl_no_cell, bool):
            # Blank row → keep scanning; anything else → we're past the students.
            if sl_no_cell is None and (usn_cell is None or not str(usn_cell).strip()):
                continue
            break
        sl_no = int(sl_no_cell)

        marks: dict[int, float | None] = {}
        for col in columns:
            if col.kind == "tot":
                continue  # derived, we won't need it
            marks[col.index] = _parse_mark(ws.cell(row=row, column=col.index))
        students.append(StudentRow(
            sl_no=sl_no,
            usn=str(usn_cell).strip() if usn_cell else "",
            marks=marks,
        ))

    co_numbers = tuple(sorted(co_numbers_seen))
    return CourseSheet(
        path=str(path),
        course_name=course_name,
        columns=tuple(columns),
        students=tuple(students),
        co_numbers=co_numbers,
    )
