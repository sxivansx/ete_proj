"""Pretty-print attainment results for the CLI.

Kept minimal (stdlib only) so we don't pull in `rich` for Phase 1.
"""
from __future__ import annotations

from .calculator import BlockCOAttainment, DirectAttainment


def _fmt(v: float | None) -> str:
    return "    —" if v is None else f"{v:6.2f}"


def _co_table(title: str, blocks: list[BlockCOAttainment], co_numbers: list[int]) -> str:
    header = f"  {'Block':<14} " + " ".join(f"  CO{co:<3}" for co in co_numbers) + "   mean"
    lines = [title, header, "  " + "-" * (len(header) - 2)]
    for b in blocks:
        row = f"  {b.label:<14} " + " ".join(_fmt(b.per_co.get(co)) for co in co_numbers)
        row += f"  {_fmt(b.mean_across_cos)}"
        lines.append(row)
    return "\n".join(lines)


def format_direct_attainment(d: DirectAttainment) -> str:
    co_numbers = sorted({co for b in d.ia_blocks for co in b.per_co})
    blocks: list[BlockCOAttainment] = [*d.ia_blocks, d.ia_average]
    if d.aat is not None:
        blocks.append(d.aat)
    blocks.append(d.cie)
    if d.see is not None:
        blocks.append(d.see)
    blocks.append(d.direct)

    out = [_co_table("CO Attainment (direct)", blocks, co_numbers)]

    # Per-question section (IA questions only — AAT/SEE already shown above).
    out.append("")
    out.append("Per-question attainment:")
    out.append(f"  {'Col':<6} {'Label':<6} {'CO tags':<10} {'max':>5} {'pass':>6} {'attempted':>10} {'attainment':>12}")
    out.append("  " + "-" * 58)
    for qs in d.per_question:
        col = qs.column
        tags = ",".join(str(t) for t in col.co_tags) if col.co_tags else "—"
        att = "    —" if qs.attainment is None else f"{qs.attainment:6.2f}"
        out.append(
            f"  {col.index:<6} {col.label:<6} {tags:<10} "
            f"{col.max_marks:>5.0f} {qs.pass_count:>6} {qs.attempt_count:>10} {att:>12}"
        )
    return "\n".join(out)
