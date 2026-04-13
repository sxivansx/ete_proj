"""Turn calculator result dataclasses into plain dicts for JSON responses."""
from __future__ import annotations

from typing import Any

from ..calculator import BlockCOAttainment, DirectAttainment, QuestionStats
from ..models import CourseSheet


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


def serialize_attainment(sheet: CourseSheet, d: DirectAttainment) -> dict[str, Any]:
    return {
        "course": {
            "name": sheet.course_name,
            "students": len(sheet.students),
            "co_numbers": list(sheet.co_numbers),
            "ia_indices": list(sheet.ia_indices()),
        },
        "per_question": [_question(q) for q in d.per_question],
        "ia_blocks": [_block(b) for b in d.ia_blocks],
        "ia_average": _block(d.ia_average),
        "aat": _block(d.aat),
        "cie": _block(d.cie),
        "see": _block(d.see),
        "direct": _block(d.direct),
    }
