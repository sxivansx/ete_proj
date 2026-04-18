"""Turn calculator result dataclasses into plain dicts for JSON responses."""
from __future__ import annotations

from typing import Any

from ..calculator import BlockCOAttainment, DirectAttainment, QuestionStats
from ..models import Column, CourseSheet


def _block(b: BlockCOAttainment | None) -> dict[str, Any] | None:
    if b is None:
        return None
    return {
        "label": b.label,
        "per_co": {str(k): v for k, v in b.per_co.items()},
        "mean": b.mean_across_cos,
    }


def _question(qs: QuestionStats) -> dict[str, Any]:
    c = qs.column
    return {
        "column_index": c.index,
        "label": c.label,
        "kind": c.kind,
        "ia_index": c.ia_index,
        "max_marks": c.max_marks,
        "co_tags": list(c.co_tags),
        "pass_count": qs.pass_count,
        "attempt_count": qs.attempt_count,
        "attainment": qs.attainment,
    }


def _column_header(c: Column) -> dict[str, Any]:
    return {
        "column_index": c.index,
        "label": c.label,
        "kind": c.kind,
        "ia_index": c.ia_index,
        "max_marks": c.max_marks,
        "co_tags": list(c.co_tags),
    }


def _student_row(student, all_columns: list[Column]) -> dict[str, Any]:
    """Serialize one student row with marks for every column (including TOT)."""
    marks: list[Any] = []
    for c in all_columns:
        raw = student.marks.get(c.index)
        marks.append(raw)
    return {
        "sl_no": student.sl_no,
        "usn": student.usn,
        "marks": marks,
    }


def serialize_attainment(sheet: CourseSheet, d: DirectAttainment) -> dict[str, Any]:
    # All columns (including TOT) for the sheet view.
    all_cols = list(sheet.columns)

    # Build student rows with marks for ALL columns (including TOT).
    # Since the calculator skips TOT columns in student.marks, we read
    # them from the original marks dict — TOT marks are still there if
    # the parser stored them; otherwise they'll be None.
    raw_students = []
    for student in sheet.students:
        marks: list[Any] = []
        for c in all_cols:
            raw = student.marks.get(c.index)
            marks.append(raw)
        raw_students.append({
            "sl_no": student.sl_no,
            "usn": student.usn,
            "marks": marks,
        })

    return {
        "course": {
            "name": sheet.course_name,
            "students": len(sheet.students),
            "co_numbers": list(sheet.co_numbers),
            "ia_indices": list(sheet.ia_indices()),
        },
        "columns": [_column_header(c) for c in all_cols],
        "raw_students": raw_students,
        "per_question": [_question(q) for q in d.per_question],
        "ia_blocks": [_block(b) for b in d.ia_blocks],
        "ia_average": _block(d.ia_average),
        "aat": _block(d.aat),
        "cie": _block(d.cie),
        "see": _block(d.see),
        "direct": _block(d.direct),
    }
