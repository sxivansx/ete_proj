"""CLI entry point for Phase 1.

Usage:
    python backend/scripts/run_attainment.py path/to/workbook.xlsx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `from app...` importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calculator import compute_direct_attainment  # noqa: E402
from app.config import CalcConfig  # noqa: E402
from app.parser import load_course_sheet  # noqa: E402
from app.report import format_direct_attainment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute CO attainment from a CIE+SEE workbook.")
    parser.add_argument("workbook", type=Path, help="Path to the faculty .xlsx file")
    parser.add_argument("--pass-fraction", type=float, default=None,
                        help="Pass threshold as a fraction of max marks (default 0.6)")
    parser.add_argument("--cie-weight", type=float, default=None,
                        help="CIE weight in Direct attainment (default 0.6)")
    args = parser.parse_args()

    if not args.workbook.exists():
        print(f"error: {args.workbook} does not exist", file=sys.stderr)
        return 2

    cfg_kwargs = {}
    if args.pass_fraction is not None:
        cfg_kwargs["pass_fraction"] = args.pass_fraction
    if args.cie_weight is not None:
        cfg_kwargs["cie_weight"] = args.cie_weight
    cfg = CalcConfig(**cfg_kwargs)

    sheet = load_course_sheet(args.workbook)
    print(f"Course:   {sheet.course_name or '(unknown)'}")
    print(f"Students: {len(sheet.students)}")
    print(f"COs:      {', '.join(f'CO{c}' for c in sheet.co_numbers)}")
    print(f"IAs:      {', '.join(f'IA{i}' for i in sheet.ia_indices())}")
    print()
    result = compute_direct_attainment(sheet, cfg)
    print(format_direct_attainment(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
