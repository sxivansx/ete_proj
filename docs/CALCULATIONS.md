# How CO Attainment is Calculated

This document describes how the tool turns a faculty CIE+SEE workbook into
the per-CO attainment numbers shown in the UI. It mirrors the math the
department does manually in Excel — the goal is *bit-for-bit parity* with
the existing sheets, not "a reasonable approximation".

> If you're changing anything in `backend/app/calculator.py` or
> `backend/app/parser.py`, read this first. If you're learning the domain,
> read `plan.md` for the derivations and then come back here.

---

## 1. The pipeline at a glance

```
              ┌──────────────┐
  .xlsx ─────►│   parser.py  │  → CourseSheet (columns + students)
              └──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │ calculator.py│  ─► QuestionStats per column
              └──────────────┘    ─► BlockCOAttainment per IA / AAT / SEE
                     │            ─► IA average → CIE → Direct
                     ▼
              ┌──────────────┐
              │serializers.py│  → JSON
              └──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   Frontend   │  → SheetView, AttainmentMatrix, etc.
              └──────────────┘
```

Three layers, sharply separated:

1. **Parser** — pure I/O. Reads cells, produces dataclasses. No math.
2. **Calculator** — pure math. Takes the dataclass, returns numbers. No I/O.
3. **API / UI** — formats numbers for display.

The boundary between (1) and (2) is enforced by `models.py` — once you have
a `CourseSheet`, the calculator has everything it needs.

---

## 2. The template contract

Every uploaded workbook must match the layout of
`backend/samples/python_programming_21ET641.xlsx` (sheet `CIE+SEE`).

| Where         | Content                                                       |
| ------------- | ------------------------------------------------------------- |
| Sheet name    | `CIE+SEE` (also accepts `Sheet1` as fallback)                 |
| Row 2, col B  | Course name (free text)                                       |
| Row 5         | Question labels (`Q1`..`Q8`, `TOT`, `TEST`, `AAT`, `FINAL`, `SEE`) |
| Row 6         | CO tag(s) per column                                          |
| Row 7         | Max marks per column                                          |
| Row 8         | Threshold (we recompute, never trust this)                    |
| Rows 10..N    | Student rows. Col A = int Sl.No, col B = USN                  |
| End of rows   | First row where col A is not an int                           |

The parser auto-detects the actual row indices by scanning for marker
cells (`Sl.No`, `Q1`, `CO's`, `Maximum Marks`), so small offsets don't
break it. But the *shape* of the layout is fixed.

### Each "question" spans two Excel columns

This trips everyone up. In the IA blocks, row 5 labels only the first
sub-column (e.g. `Q1` in col C, blank in col D), but rows 6 and 7 carry
*independent* CO tags and max marks for **each** sub-column.

The parser treats the unlabeled sub-column as its own `Column`, inheriting
the label of the preceding labeled one. So `Q1` in the dataclass world is
actually two `Column` records.

### CO tag parsing is forgiving

Row 6 can be:

- A single integer: `2`
- A comma / space list: `"2,3"`, `"1 3"`
- Free-form: `"CO 1 2 3 4"` (common in AAT / SEE columns)

The parser extracts every integer it finds. Empty cells = no CO tags.

### Blanks vs text

- **Blank cell** = student did not attempt. Excluded from both pass count
  and attempt count.
- **Number** = numeric mark. Counted as attempted; counted as passing if
  ≥ threshold.
- **Text** (e.g. `"NE"` for Not Eligible) = attempted, but cannot satisfy
  `≥ threshold`. Counted as attempted, never as passing.

This matches Excel's `COUNTIF(range, "<>")` (counts any non-blank, including
text) and `COUNTIF(range, ">=threshold")` (only numeric matches).

---

## 3. Per-question attainment

For each question column `c` with max marks `M`:

```
threshold      = pass_fraction * M           # default pass_fraction = 0.6
pass_count     = #students with mark ≥ threshold
attempt_count  = #students with any non-blank value
attainment(c)  = pass_count * 100 / attempt_count   (None if attempt_count == 0)
```

Implementation: `question_stats()` in `calculator.py:65`.

The `pass_fraction` lives on `CalcConfig` and defaults to `0.6` (matches
the row 8 formula `=0.6 * C7` in the sheet). Callers can override it.

---

## 4. Per-IA per-CO attainment

For one IA block `i` and CO `k`, the per-CO attainment is the **arithmetic
mean of the per-question attainments** for every question column in IA `i`
tagged with CO `k`:

```
ia_co(i, k) = mean( attainment(c) for c in IA_i_questions if k in c.co_tags )
```

Columns where `attainment` is `None` (nobody attempted) are skipped, not
treated as zero.

This matches the Excel `SUMIF(mask, 1, row106) / COUNTIF(mask, 1)` formula
on `CO-Attainment` sheet.

Implementation: `_co_attainment_from_columns()` in `calculator.py:91`.

---

## 5. IA average (the pooled mean — important!)

The "IA average" line in the output is **not** the mean of `ia_co(1, k)`,
`ia_co(2, k)`, `ia_co(3, k)`. It's the pooled mean across **every IA
question column** tagged with CO `k`:

```
ia_avg(k) = mean( attainment(c) for c in ALL_IA_questions if k in c.co_tags )
```

These two formulas only coincide when each IA has the same number of
CO-`k`-tagged questions. They generally don't, and the difference is real
(~1% on CO2 / CO3 in the sample workbook). We tried mean-of-means first;
it was wrong.

Implementation: `compute_direct_attainment()` in `calculator.py:184`.

---

## 6. AAT (Activity-based Assessment Tool)

The AAT column is a **single column** that contributes to multiple COs at
once. Its attainment number is the same for every CO it's tagged with:

```
aat(k) = attainment(AAT_column)   if k in AAT_column.co_tags else None
```

If the AAT column is untagged (rare but possible), it's treated as
covering every CO uniformly.

Implementation: `_block_from_single_column()` in `calculator.py:116`.

---

## 7. CIE — combine IAs with AAT

The CIE per-CO attainment is the elementwise mean of the IA average and
the AAT block:

```
cie(k) = mean( ia_avg(k), aat(k) )    # skipping any None
```

If AAT is missing, CIE = IA average. If IA average is missing for that CO,
CIE = AAT.

This matches `=SUM(C4:C5)/COUNTIF(C4:C5,"<>")` on the CO-Attainment sheet.

Implementation: `_mean_blocks()` in `calculator.py:133`.

---

## 8. SEE — Semester-End Examination

Same shape as AAT: single column, attainment shared across every CO it's
tagged with. Default tagging covers all COs uniformly (rows 11..14 col K..N
on `CO-Attainment` all reference `CIE+SEE!AZ106`).

---

## 9. Direct attainment

The published "Direct CO Attainment" weights CIE and SEE:

```
direct(k) = cie(k) * cie_weight + see(k) * (1 - cie_weight)
```

`cie_weight` defaults to `0.6` → 60% CIE + 40% SEE. Override via
`CalcConfig`.

Edge cases:
- If both CIE and SEE are `None` for a CO, direct is `None`.
- If only one side exists, direct = that side (no weighting).

Implementation: `_weighted_blocks()` in `calculator.py:143`.

---

## 10. Final attainment (Direct + Indirect)

When indirect attainment (course-end survey) is added later:

```
final(k) = direct(k) * direct_weight + indirect(k) * (1 - direct_weight)
```

`direct_weight` defaults to `0.9` → 90% direct + 10% indirect.

Implementation: `compute_final_attainment()` in `calculator.py:236`.

This isn't wired into the UI yet — it's there for when Phase 4 brings in
the survey data.

---

## 11. The default knobs

All in `backend/app/config.py`:

| Knob              | Default | Meaning                                |
| ----------------- | ------- | -------------------------------------- |
| `pass_fraction`   | 0.6     | mark ≥ 60% of max = "passed"           |
| `cie_weight`      | 0.6     | Direct = 0.6·CIE + 0.4·SEE             |
| `direct_weight`   | 0.9     | Final  = 0.9·Direct + 0.1·Indirect     |

All bounded to `[0, 1]` — `CalcConfig.__post_init__` raises on bad input.

---

## 12. Worked example

Course = Python Programming (21ET641), one CO (CO1) for brevity.

```
IA1: Q1a (max 10, CO1)  →  18/20 attempted, 14 ≥ 6  → 14·100/18  = 77.78%
     Q1b (max 5,  CO1)  →  18/20 attempted, 11 ≥ 3  → 11·100/18  = 61.11%
     Q4a (max 10, CO1)  →  17/20 attempted,  9 ≥ 6  →  9·100/17  = 52.94%

IA2: Q3a (max 10, CO1)  →  19/20 attempted, 12 ≥ 6  → 12·100/19  = 63.16%

IA3: (no CO1 questions)

AAT: (max 10, CO1)      →  20/20 attempted, 16 ≥ 6  → 16·100/20  = 80.00%
SEE: (max 100, CO1)     →  19/20 attempted, 13 ≥ 60 → 13·100/19  = 68.42%
```

Per-IA per-CO:
```
ia_co(1, 1) = mean(77.78, 61.11, 52.94)   = 63.94%
ia_co(2, 1) = mean(63.16)                  = 63.16%
ia_co(3, 1) = None
```

Pooled IA average for CO1:
```
ia_avg(1) = mean(77.78, 61.11, 52.94, 63.16) = 63.75%
```
*(Note: not the mean of `63.94` and `63.16` = 63.55%. Three IA1 questions
vs. one IA2 question, so the pooled mean weights toward IA1.)*

CIE:
```
cie(1) = mean(63.75, 80.00) = 71.88%
```

Direct:
```
direct(1) = 0.6 · 71.88 + 0.4 · 68.42 = 70.50%
```

These are the numbers the UI displays in the AttainmentMatrix.

---

## 13. Known divergences from the faculty sheet

There's a **bug in the faculty template**: `CO-Attainment!C4` references
`CIE+SEE!AX113` (the mean across CO1..CO4) instead of `AX109` (the CO1
aggregate). This leaks into the CIE and Direct values shown for CO1 on
the `CO-Attainment` sheet.

**Our calculator uses the correct per-CO value.** Expect a ~1% difference
on CO1 vs. what the faculty's sheet displays. Every other CO matches to
within `1e-9`.

---

## 14. Cross-checking

The other sheets in the workbook (`CO-Attainment`, `PO-Attainment (2)`,
etc.) carry the manually-computed numbers. We **never read those as input**
— they're for human cross-checking only.

When debugging a divergence:

1. Run the CLI:
   ```bash
   python backend/scripts/run_attainment.py backend/samples/python_programming_21ET641.xlsx
   ```
2. Open the workbook, go to `CO-Attainment`, compare per-CO values.
3. If they disagree by more than a rounding error, check the formula in
   the cell. Often it's the AX113 / AX109 bug above, or the calculator
   correctly handling a `None` that the sheet treats as zero.

---

## 15. Where to look in the code

| Concept                       | File                              | Symbol                              |
| ----------------------------- | --------------------------------- | ----------------------------------- |
| Threshold / weight defaults   | `backend/app/config.py`           | `CalcConfig`                        |
| `Column` / `StudentRow`       | `backend/app/models.py`           | dataclasses                         |
| Workbook → `CourseSheet`      | `backend/app/parser.py`           | `load_course_sheet()`               |
| Per-question pass / attempt   | `backend/app/calculator.py:65`    | `question_stats()`                  |
| Per-IA per-CO mean            | `backend/app/calculator.py:91`    | `_co_attainment_from_columns()`     |
| AAT / SEE single-column block | `backend/app/calculator.py:116`   | `_block_from_single_column()`       |
| CIE = mean(IA, AAT)           | `backend/app/calculator.py:133`   | `_mean_blocks()`                    |
| Direct = w·CIE + (1-w)·SEE    | `backend/app/calculator.py:143`   | `_weighted_blocks()`                |
| End-to-end pipeline           | `backend/app/calculator.py:170`   | `compute_direct_attainment()`       |
| JSON serialization            | `backend/app/api/serializers.py`  | —                                   |
| UI tables                     | `frontend/src/components/AttainmentMatrix.tsx` | —                      |
| Per-question UI               | `frontend/src/components/QuestionTable.tsx` | —                         |
