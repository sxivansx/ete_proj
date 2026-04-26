"""Pure attainment math.

Every function here takes a parsed :class:`CourseSheet` (plus an optional
:class:`CalcConfig`) and returns numbers. No I/O, no state.

The math mirrors the faculty's CIE+SEE / CO-Attainment sheets exactly —
see ``docs/plan.md`` for the derivations.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import CalcConfig
from .models import Column, CourseSheet


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QuestionStats:
    column: Column
    pass_count: int
    attempt_count: int

    @property
    def attainment(self) -> float | None:
        """``pass * 100 / attempted``, or ``None`` if nobody attempted."""
        if self.attempt_count == 0:
            return None
        return self.pass_count * 100.0 / self.attempt_count


@dataclass(frozen=True)
class BlockCOAttainment:
    """Per-CO attainment for one IA / AAT / SEE block."""

    label: str                       # "IA1", "AAT", "SEE", ...
    per_co: dict[int, float | None]  # co_number -> attainment

    @property
    def mean_across_cos(self) -> float | None:
        vals = [v for v in self.per_co.values() if v is not None]
        return sum(vals) / len(vals) if vals else None


@dataclass(frozen=True)
class DirectAttainment:
    """End-to-end direct CO attainment for one course."""

    per_question: tuple[QuestionStats, ...]
    ia_blocks: tuple[BlockCOAttainment, ...]      # one per IA
    ia_average: BlockCOAttainment                 # avg across IAs (aka IA attainment)
    aat: BlockCOAttainment | None
    cie: BlockCOAttainment                        # mean(ia_average, aat)
    see: BlockCOAttainment | None
    direct: BlockCOAttainment                     # cie*w + see*(1-w)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def question_stats(column: Column, sheet: CourseSheet, cfg: CalcConfig) -> QuestionStats:
    """Compute pass / attempt counts for a single question column.

    Matches Excel semantics:
      - ``COUNTIF(range, "<>")`` counts any non-blank cell (numbers AND text).
        A string like ``"NE"`` (Not Eligible) is therefore counted as attempted.
      - ``COUNTIF(range, ">=threshold")`` only matches numeric cells, so
        non-numeric "attempts" never count towards the pass count.
    """
    threshold = cfg.pass_fraction * column.max_marks
    pass_count = 0
    attempt_count = 0
    for student in sheet.students:
        mark = student.marks.get(column.index)
        if mark is None:
            continue  # blank = not attempted
        attempt_count += 1
        if isinstance(mark, (int, float)) and mark >= threshold:
            pass_count += 1
    return QuestionStats(column=column, pass_count=pass_count, attempt_count=attempt_count)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _co_attainment_from_columns(
    columns: list[Column],
    stats_by_col: dict[int, QuestionStats],
    co_numbers: tuple[int, ...],
) -> dict[int, float | None]:
    """Average per-question attainments into per-CO attainments.

    For each CO, pick all question columns tagged with that CO and take the
    arithmetic mean of their attainments (ignoring any column where nobody
    attempted). Questions with no attempt get skipped, not counted as zero.
    """
    per_co: dict[int, float | None] = {}
    for co in co_numbers:
        vals: list[float] = []
        for col in columns:
            if co not in col.co_tags:
                continue
            qs = stats_by_col.get(col.index)
            if qs is None or qs.attainment is None:
                continue
            vals.append(qs.attainment)
        per_co[co] = _mean(vals)
    return per_co


def _block_from_single_column(
    column: Column,
    stats: QuestionStats,
    co_numbers: tuple[int, ...],
    label: str,
) -> BlockCOAttainment:
    """A single-column block (AAT / SEE): the same attainment applies to every CO
    that column is tagged with. If it's tagged to all COs, all get the same
    number."""
    attainment = stats.attainment
    per_co: dict[int, float | None] = {}
    tags = column.co_tags or co_numbers  # untagged -> treat as covering all COs
    for co in co_numbers:
        per_co[co] = attainment if co in tags else None
    return BlockCOAttainment(label=label, per_co=per_co)


def _mean_blocks(label: str, blocks: list[BlockCOAttainment], co_numbers: tuple[int, ...]) -> BlockCOAttainment:
    """Element-wise mean of several blocks, skipping ``None`` entries."""
    per_co: dict[int, float | None] = {}
    for co in co_numbers:
        vals = [b.per_co.get(co) for b in blocks]
        vals = [v for v in vals if v is not None]
        per_co[co] = _mean(vals)
    return BlockCOAttainment(label=label, per_co=per_co)


def _weighted_blocks(
    label: str,
    primary: BlockCOAttainment,
    primary_weight: float,
    secondary: BlockCOAttainment | None,
    co_numbers: tuple[int, ...],
) -> BlockCOAttainment:
    """``primary * w + secondary * (1 - w)``; if secondary is missing, return primary."""
    per_co: dict[int, float | None] = {}
    for co in co_numbers:
        p = primary.per_co.get(co)
        s = secondary.per_co.get(co) if secondary is not None else None
        if p is None and s is None:
            per_co[co] = None
        elif s is None:
            per_co[co] = p
        elif p is None:
            per_co[co] = s
        else:
            per_co[co] = p * primary_weight + s * (1.0 - primary_weight)
    return BlockCOAttainment(label=label, per_co=per_co)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_direct_attainment(
    sheet: CourseSheet,
    cfg: CalcConfig | None = None,
) -> DirectAttainment:
    """Run the full per-question / per-CO / direct attainment pipeline."""
    cfg = cfg or CalcConfig()
    co_numbers = sheet.co_numbers

    # --- Per-question stats ---------------------------------------------------
    assessable = [c for c in sheet.columns if c.kind in ("question", "aat", "see")]
    per_q: list[QuestionStats] = [question_stats(c, sheet, cfg) for c in assessable]
    stats_by_col = {qs.column.index: qs for qs in per_q}

    # --- Per-IA per-CO --------------------------------------------------------
    ia_blocks: list[BlockCOAttainment] = []
    for ia in sheet.ia_indices():
        q_cols = [c for c in sheet.columns if c.kind == "question" and c.ia_index == ia]
        per_co = _co_attainment_from_columns(q_cols, stats_by_col, co_numbers)
        ia_blocks.append(BlockCOAttainment(label=f"IA{ia}", per_co=per_co))

    # ``IA average`` pools ALL IA question columns tagged with each CO and
    # averages their attainments directly — this matches the Excel
    # ``SUMIF(mask, 1, row106) / COUNTIF(mask, 1)`` roll-up. Averaging the
    # per-IA means would only equal this when each IA has the same number of
    # questions tagged to that CO, which is generally not the case.
    all_ia_question_cols = [c for c in sheet.columns if c.kind == "question"]
    ia_average = BlockCOAttainment(
        label="IA average",
        per_co=_co_attainment_from_columns(all_ia_question_cols, stats_by_col, co_numbers),
    )

    # --- AAT / SEE (single-column) -------------------------------------------
    aat_col = sheet.column("aat")
    aat_block = (
        _block_from_single_column(aat_col, stats_by_col[aat_col.index], co_numbers, "AAT")
        if aat_col is not None and aat_col.index in stats_by_col
        else None
    )

    see_col = sheet.column("see")
    see_block = (
        _block_from_single_column(see_col, stats_by_col[see_col.index], co_numbers, "SEE")
        if see_col is not None and see_col.index in stats_by_col
        else None
    )

    # --- CIE (mean of IA average and AAT) ------------------------------------
    cie_sources = [ia_average] + ([aat_block] if aat_block is not None else [])
    cie_block = _mean_blocks("CIE", cie_sources, co_numbers)

    # --- Direct (CIE * w + SEE * (1 - w)) ------------------------------------
    direct_block = _weighted_blocks(
        "Direct", cie_block, cfg.cie_weight, see_block, co_numbers,
    )

    return DirectAttainment(
        per_question=tuple(per_q),
        ia_blocks=tuple(ia_blocks),
        ia_average=ia_average,
        aat=aat_block,
        cie=cie_block,
        see=see_block,
        direct=direct_block,
    )


def compute_final_attainment(
    direct: BlockCOAttainment,
    indirect: BlockCOAttainment,
    cfg: CalcConfig | None = None,
) -> BlockCOAttainment:
    """``Direct * w + Indirect * (1 - w)`` per CO."""
    cfg = cfg or CalcConfig()
    co_numbers = tuple(sorted(set(direct.per_co) | set(indirect.per_co)))
    return _weighted_blocks("Final", direct, cfg.direct_weight, indirect, co_numbers)
