"""Unit + regression tests for the CO Attainment calculator."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calculator import (
    BlockCOAttainment,
    compute_direct_attainment,
    compute_final_attainment,
    question_stats,
)
from app.config import CalcConfig
from app.models import Column, CourseSheet, StudentRow
from app.parser import _parse_co_tags, load_course_sheet


SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "python_programming_21ET641.xlsx"


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

class TestParseCoTags:
    def test_none(self):
        assert _parse_co_tags(None) == ()

    def test_int(self):
        assert _parse_co_tags(2) == (2,)

    def test_comma_string(self):
        assert _parse_co_tags("2,3") == (2, 3)

    def test_space_string(self):
        assert _parse_co_tags("1 3") == (1, 3)

    def test_co_prefix(self):
        assert _parse_co_tags("CO 1 2 3 4") == (1, 2, 3, 4)

    def test_empty_string(self):
        assert _parse_co_tags("") == ()


# ---------------------------------------------------------------------------
# Pure-math unit tests (no Excel needed)
# ---------------------------------------------------------------------------

def _make_sheet(co_numbers=(1, 2)) -> CourseSheet:
    """Small synthetic sheet: one IA with two questions (Q1 -> CO1, Q2 -> CO2)."""
    q1 = Column(index=3, kind="question", label="Q1", max_marks=10.0,
                co_tags=(1,), ia_index=1)
    q2 = Column(index=4, kind="question", label="Q2", max_marks=10.0,
                co_tags=(2,), ia_index=1)
    students = (
        StudentRow(1, "S1", {3: 8.0, 4: 5.0}),     # pass Q1, fail Q2
        StudentRow(2, "S2", {3: 6.0, 4: None}),    # pass Q1, didn't attempt Q2
        StudentRow(3, "S3", {3: 2.0, 4: 9.0}),     # fail Q1, pass Q2
    )
    return CourseSheet(path=":memory:", course_name="TEST",
                       columns=(q1, q2), students=students, co_numbers=co_numbers)


class TestQuestionStats:
    def test_default_threshold(self):
        sheet = _make_sheet()
        q1 = sheet.columns[0]
        qs = question_stats(q1, sheet, CalcConfig())
        # threshold = 6.0. Marks: 8, 6, 2 → 2 pass, 3 attempted.
        assert qs.attempt_count == 3
        assert qs.pass_count == 2
        assert qs.attainment == pytest.approx(2 * 100 / 3)

    def test_blank_not_counted_as_attempt(self):
        sheet = _make_sheet()
        q2 = sheet.columns[1]
        qs = question_stats(q2, sheet, CalcConfig())
        # Marks: 5, None, 9 → 2 attempted, 1 pass (9 ≥ 6).
        assert qs.attempt_count == 2
        assert qs.pass_count == 1
        assert qs.attainment == pytest.approx(50.0)

    def test_custom_pass_fraction(self):
        sheet = _make_sheet()
        q1 = sheet.columns[0]
        qs = question_stats(q1, sheet, CalcConfig(pass_fraction=0.5))
        # threshold = 5.0. Marks 8, 6, 2 → 2 pass.
        assert qs.pass_count == 2


class TestDirectAttainment:
    def test_per_co_average(self):
        sheet = _make_sheet()
        result = compute_direct_attainment(sheet)
        # Only one IA, so IA1 == IA average.
        assert len(result.ia_blocks) == 1
        ia1 = result.ia_blocks[0]
        assert ia1.per_co[1] == pytest.approx(2 * 100 / 3)
        assert ia1.per_co[2] == pytest.approx(50.0)
        # No AAT / SEE in synthetic sheet → CIE == IA average, Direct == CIE.
        assert result.aat is None
        assert result.see is None
        assert result.cie.per_co == ia1.per_co
        assert result.direct.per_co == ia1.per_co


class TestFinalAttainment:
    def test_weighted(self):
        direct = BlockCOAttainment("Direct", {1: 80.0, 2: 60.0})
        indirect = BlockCOAttainment("Indirect", {1: 90.0, 2: 70.0})
        final = compute_final_attainment(direct, indirect)
        # 0.9 * direct + 0.1 * indirect
        assert final.per_co[1] == pytest.approx(0.9 * 80 + 0.1 * 90)
        assert final.per_co[2] == pytest.approx(0.9 * 60 + 0.1 * 70)

    def test_missing_indirect_falls_back_to_direct(self):
        direct = BlockCOAttainment("Direct", {1: 80.0})
        indirect = BlockCOAttainment("Indirect", {1: None})
        final = compute_final_attainment(direct, indirect)
        assert final.per_co[1] == pytest.approx(80.0)


# ---------------------------------------------------------------------------
# Regression test against the real faculty sample
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not SAMPLE.exists(), reason=f"sample workbook missing at {SAMPLE}")
class TestSampleWorkbook:
    @pytest.fixture(scope="class")
    def sheet(self) -> CourseSheet:
        return load_course_sheet(SAMPLE)

    @pytest.fixture(scope="class")
    def result(self, sheet: CourseSheet):
        return compute_direct_attainment(sheet)

    def test_structure(self, sheet: CourseSheet):
        assert "PYTHON" in sheet.course_name.upper()
        assert sheet.co_numbers == (1, 2, 3, 4)
        assert sheet.ia_indices() == (1, 2, 3)
        # 94 students in the template (rows 10..103).
        assert len(sheet.students) == 94

    def test_special_columns_detected(self, sheet: CourseSheet):
        assert sheet.column("test") is not None
        assert sheet.column("aat") is not None
        assert sheet.column("final") is not None
        assert sheet.column("see") is not None

    def test_per_co_attainment_in_range(self, result):
        """All computed attainments should be between 0 and 100."""
        for ia in result.ia_blocks:
            for v in ia.per_co.values():
                assert v is None or 0.0 <= v <= 100.0
        for v in result.direct.per_co.values():
            assert v is None or 0.0 <= v <= 100.0

    def test_ia_average_matches_excel(self, result):
        """IA per-CO attainment must match the values Excel computes in AX109..AX112.

        The sheet computes CO-k's IA attainment as
        ``SUMIF(mask, 1, row106) / COUNTIF(mask, 1)`` — a pooled average over
        every IA question column tagged with CO-k. Numbers extracted from the
        sample workbook with ``data_only=True``.
        """
        expected = {
            1: 66.80453320917795,
            2: 65.47805174447564,
            3: 65.61915936137189,
            4: 76.3157894736842,
        }
        for co, exp in expected.items():
            got = result.ia_average.per_co[co]
            assert got == pytest.approx(exp, rel=1e-9), f"CO{co}: {got} != {exp}"

    def test_aat_and_see_match_excel(self, result):
        # AAT attainment (col AX, row 106) and SEE attainment (col AZ, row 106)
        # from the sample workbook.
        assert result.aat.per_co[1] == pytest.approx(97.84946236559139, rel=1e-9)
        assert result.see.per_co[1] == pytest.approx(36.144578313253014, rel=1e-9)

    def test_direct_matches_weighted_cie_and_see(self, result):
        """Direct[CO] should equal cie_weight*CIE[CO] + (1-cie_weight)*SEE[CO]."""
        cfg = CalcConfig()
        for co, direct_v in result.direct.per_co.items():
            cie_v = result.cie.per_co.get(co)
            see_v = result.see.per_co.get(co) if result.see else None
            if direct_v is None:
                continue
            if cie_v is not None and see_v is not None:
                expected = cfg.cie_weight * cie_v + (1 - cfg.cie_weight) * see_v
                assert direct_v == pytest.approx(expected, rel=1e-9)
