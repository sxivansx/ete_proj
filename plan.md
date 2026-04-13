# CO Attainment Automation — Project Plan

A department tool that automates the Excel-based CO (Course Outcome) attainment
calculations currently done by hand. We grow it in phases: start with a
rock-solid Python core that mirrors the existing spreadsheet math, then wrap it
in an API + React dashboard, persist to a DB, and finally dockerise for
on-prem deployment.

---

## Template contract (READ FIRST)

**This project only works if every uploaded workbook follows the same
layout.** Faculty sheets today vary subtly (merged cells, label casing,
extra columns) and the tool cannot guess intent. We commit to a single
**canonical template** and reject anything that doesn't match it.

### Option we are going with
Adopt `backend/samples/python_programming_21ET641.xlsx` as the **canonical
template v1**. Everything the parser / calculator / API assume is derived
from this one file. If faculty want their existing sheets automated, they
copy their marks into this template.

### Why a hard template (and not "auto-detect anything")
- The layout has real ambiguity — a CIE question spans two Excel columns,
  row-5 labels are sparse, CO tags are sometimes numbers and sometimes
  strings like `"CO 1 2 3 4"`. Auto-detection across arbitrary sheets is a
  research problem, not a feature we want to own.
- Every attainment number depends on *which* rows hold student marks and
  *which* row holds the CO tag. Guessing wrong silently produces wrong
  numbers — the worst possible failure mode.
- A fixed template lets us write a clear validator: "row 5 = labels, row
  6 = CO tags, row 7 = max marks, students start row 10, stop at the first
  non-int Sl.No". A malformed upload fails loudly with a pointer to the bad
  row/column.

### What the canonical template v1 locks in
Sheet named `CIE+SEE` with this layout (1-indexed):
| Row / Col | Meaning |
|---|---|
| Row 2, col B | Course name (free text) |
| Row 4 | Section banners (`INTERNAL ASSESMENT-1`, etc.) — parser ignores |
| Row 5 | Question label (`Q1`..`Q8`), plus `TOT`, `TEST`, `AAT (ASSGN)`, `FINAL`, `SEE` |
| Row 6 | CO tag per column — int, `"2,3"`, `"1 3"`, or `"CO 1 2 3 4"` |
| Row 7 | Max marks per column |
| Row 8 | Per-column pass threshold (we recompute; sheet value ignored) |
| Row 9 | Header strip (`Sl.No`, `USN`) |
| Rows 10..N | Student rows — col A is int Sl.No, col B is USN, then marks |
| First non-int Sl.No | End of students (summary rows start here) |

Per IA block (columns):
- 8 questions × 2 sub-columns each = 16 columns
- 1 `TOT` column terminates the IA (parser uses this to advance IA counter)

Trailing columns (after the three IA blocks):
- `TEST` — derived, ignored by the calculator
- `AAT (ASSGN)` — 20 marks, CO-tagged to one or all COs
- `FINAL` — derived, ignored
- `SEE` — 100 marks, tagged to all COs

The other sheets (`CO-PO Mapping`, `CO-Attainment`, `CES`, `PO-Attainment`)
are read-only references — we **recompute** everything from `CIE+SEE` and
write our own results; we don't trust the displayed values in those sheets.

### Obligations that fall out of this
- **Phase 1 (now):** parser raises a clear error for missing sheet names,
  missing row 5 labels where required, students with non-numeric Sl.No
  anywhere except the end, and CO tags that reference a CO number not
  declared on the `CO-PO Mapping` sheet.
- **Phase 2 (API):** `POST /api/v1/sheets/upload` runs a schema validator
  and returns structured errors (row + column + human message) when the
  upload doesn't match the template.
- **Phase 3 (UI):** download button for the canonical template so faculty
  never hand-roll it.
- **Template versioning:** when we change the layout (e.g. to support 5 COs
  or a different SEE weight), bump the version in `backend/app/config.py`
  and ship a migration note in `CHANGELOG.md`.

---

## Domain primer (the math we are automating)

Reference sheet: `backend/samples/python_programming_21ET641.xlsx`, sheet
`CIE+SEE`.

### Assessment structure
- **3 CIEs (IA1, IA2, IA3)** — each has 8 questions, 50 marks total.
  - Q1 and Q2 are compulsory.
  - Student picks one of (Q3 OR Q4), one of (Q5 OR Q6), **and** does (Q7 AND Q8).
  - So a student answers 5 questions → blanks are legitimate "not attempted".
- **AAT (Assignment / Alternative Assessment Test)** — 20 marks, can target one
  CO or span all of them. The CO tag for AAT lives in row 6 (e.g. `"CO 1 2 3 4"`).
- **SEE (Semester End Exam)** — 100 marks, tagged against all COs.
- **CES** — indirect feedback survey (used only in the final roll-up).

### Per-question CO tagging
Row 6 of `CIE+SEE` holds the CO number for each question column. A cell may be
a single integer (`2`) or a comma-list (`"2,3"`) when a question covers
multiple COs. The sample has 4 COs (CO1..CO4).

### Per-question attainment
For each question column `q`, with threshold `T_q = 0.6 * max_marks_q`:
- `pass_count_q  = COUNTIF(marks, ">= T_q)"`
- `attempt_count_q = COUNTIF(marks, "<>")`   *(non-blank)*
- `attainment_q = pass_count_q * 100 / attempt_count_q`

(Rows 104, 105, 106 in the sheet.)

### Per-CO attainment per IA
For each CO `k` (1..4), look at every question column tagged with `k` and take
the **average** of those `attainment_q` values. In Excel this is rows
109..112 (the 0/1 membership mask) and column `AX` which does the
`SUMIF / COUNTIF` roll-up. Row 113 is the average across CO1..CO4 for the
whole IA block.

### CIE CO-Attainment (direct)
For each CO:
```
CIE_CO_k = mean( IA_CO_k , AAT_CO_k )      # simple mean of non-blank entries
```
Sheet reference: `CO-Attainment` rows 4..6.

### SEE CO-Attainment
`SEE_CO_k` is the per-question attainment of the SEE column (`AZ106`), applied
identically to every CO (the SEE is tagged to all COs).

### Direct CO-Attainment (CIE + SEE)
```
Direct_CO_k = 0.6 * CIE_CO_k + 0.4 * SEE_CO_k
```

### Final CO-Attainment (direct + indirect)
```
Final_CO_k = 0.9 * Direct_CO_k + 0.1 * Indirect_CO_k     # CES survey
```

### CO-PO mapping (for PO attainment — later phase)
Sheet `CO-PO Mapping` rows 5..8 hold each CO's weight (1/2/3) against PO1..PO11,
PSO1..PSO3. PO attainment is the weighted avg of final CO attainments — we
defer this to Phase 2.

### Configurable knobs (should NOT be hard-coded)
- CIE pass threshold fraction (default `0.6`).
- Direct weighting: CIE `0.6` / SEE `0.4`.
- Final weighting: direct `0.9` / indirect `0.1`.
- Number of COs (sample has 4; other courses may vary).
- Number of IAs (default 3).
- Per-question max marks (read from row 7 of the sheet).

---

## Phased roadmap

Each phase must be runnable end-to-end on its own before we start the next.

### Phase 1 — Python core CO Attainment engine  ✅ done
Deliverable: a CLI that reads the canonical template and prints per-question
attainment, per-IA per-CO attainment, and direct CO attainment that match
the Excel-computed numbers.

Scope:
- `backend/app/config.py` — constants, thresholds, template version.
- `backend/app/models.py` — `Column`, `StudentRow`, `CourseSheet` dataclasses.
- `backend/app/parser.py` — `load_course_sheet(path) -> CourseSheet`, strict
  to the canonical template.
- `backend/app/calculator.py` — pure functions: `question_stats`,
  `compute_direct_attainment`, `compute_final_attainment`.
- `backend/app/report.py` — pretty table output for the CLI.
- `backend/scripts/run_attainment.py` — CLI entry point.
- `backend/tests/test_calculator.py` — unit tests + a regression test that
  loads the sample workbook and pins numbers to Excel-computed values.

**Follow-up still owed (Phase 1.5 — do before Phase 2):**
- Promote the "canonical template" from a convention to an enforced
  contract: `backend/app/template.py` with `validate(workbook)` that
  reports every layout violation (missing sheet, missing label, wrong
  row count, unknown CO in row 6, non-int Sl.No inside the student range,
  sub-column without max-marks, etc.).
- Ship the empty canonical template as `backend/samples/template_v1.xlsx`
  (strip the student rows out of the Python Programming file) so faculty
  can download-and-fill.
- Unit tests for the validator on a handful of broken workbooks
  (missing row 5 label, wrong sheet name, extra column, truncated IA).

Non-goals for Phase 1: no web server, no DB, no React, no PO attainment,
no writing back to Excel.

### Phase 2 — FastAPI backend  ✅ minimal done
Done:
- `GET  /api/v1/health` — liveness check.
- `POST /api/v1/upload` — accepts `.xlsx` (multipart), runs the parser +
  calculator, returns the full attainment payload as JSON. Query params
  `pass_fraction` and `cie_weight` override the defaults.

Still owed:
- `GET  /api/v1/template` — download the canonical `template_v1.xlsx`.
- Persist uploads (paired with Phase 4 DB work): `POST /api/v1/sheets/upload`
  returning a sheet ID; `GET /api/v1/sheets/{id}/attainment`;
  `GET /api/v1/sheets/{id}/questions`.
- `PATCH /api/v1/sheets/{id}/questions/{qid}` to override the CO tag for a
  question. Override stored alongside the upload, not back in the xlsx.
- Structured 422 payloads from the template validator (Phase 1.5) listing
  every layout violation with row + column + human message.
- PO attainment calculation (uses `CO-PO Mapping` sheet).

### Phase 3 — React dashboard  ✅ minimal done
Done:
- Vite + React + TypeScript scaffold under `frontend/`, installed with Bun.
- Drag-and-drop uploader, error panel, summary card, per-CO attainment
  matrix (IA1..IA3, IA average, AAT, CIE, SEE, Direct — green ≥60% / red
  <60%), per-question breakdown table (paginated).
- Vite dev proxy routes `/api/*` to the FastAPI backend.

Still owed:
- **Template tab** — prominent "Download blank template" button + short
  "how to fill" note so faculty never hand-roll the xlsx.
- Structured validation error display (when Phase 1.5 ships): show each
  violation inline (row + column + message) instead of a raw detail string.
- **Sheet view** — tabular student marks (read-only).
- **Bar charts** — per-CO bar charts per IA, CIE, SEE, Direct. Red/green
  vs the course target (80% from `CO-PO Mapping`).
- **CO override UI** — editable CO tag per question that writes through
  the `PATCH` endpoint once that lands.
- **Export** — "Download results as .xlsx" that re-injects computed values
  into a copy of the canonical template so faculty can submit the familiar
  sheet.

### Phase 4 — Database persistence
- Postgres via SQLAlchemy + Alembic.
- Schema (first cut):
  - `courses` (code, name, semester, batch, year)
  - `assessments` (course_id, type=IA|AAT|SEE, index, max_marks)
  - `questions` (assessment_id, number, max_marks, co_tags JSONB)
  - `students` (usn, name, batch)
  - `responses` (student_id, question_id, marks)
  - `attainment_snapshots` (course_id, computed_at, payload JSONB) — keep the
    full calc output for auditing.
- Faculty auth (later): start with a single-user HTTP-basic or shared token;
  move to real auth if the tool sees multi-user use.

### Phase 5 — Dockerise & deploy
- Multi-stage `backend/Dockerfile` (builder + slim runtime).
- `frontend/Dockerfile` — vite build → nginx static.
- `docker-compose.yml` — api + web + postgres + a named volume for uploads.
- `.env.example` documenting every knob.
- One-command bring-up: `docker compose up -d`.
- Deploy target: user's own server. Document:
  - Reverse proxy config (Caddy or nginx).
  - Backup of the postgres volume + `data/uploads/`.
  - How to update (pull image → `docker compose up -d`).

---

## Repo layout (target)
```
ete-proj/
├── plan.md
├── CLAUDE.md                    # living project context for Claude
├── README.md                    # user-facing quickstart (Phase 5)
├── data/                        # runtime artifacts (gitignored later)
│   └── uploads/
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── parser.py
│   │   ├── calculator.py
│   │   ├── report.py
│   │   └── api/                 # Phase 2
│   ├── scripts/
│   │   └── run_attainment.py
│   ├── samples/
│   │   └── python_programming_21ET641.xlsx
│   └── tests/
├── frontend/                    # Phase 3
└── docker-compose.yml           # Phase 5
```

## Testing strategy
- **Phase 1:** unit tests on the pure calculator + one regression test that
  loads the sample workbook and asserts expected numbers (we precompute them
  by opening the xlsx with `data_only=True`).
- **Phase 2:** API integration tests with `httpx.AsyncClient`.
- **Phase 3:** playwright smoke for the upload → dashboard happy path.
- **Phase 5:** `docker compose up` in CI, hit `/healthz`.

## Open questions (park and revisit)
- Do we need to support courses with more/fewer than 4 COs? Assume yes —
  the calculator already derives CO numbers from row 6. The template
  itself is CO-count agnostic; a 5-CO course just has more distinct
  row-6 values.
- Do we need to support more/fewer than 3 IAs? Defer — but the parser
  already advances IA on each `TOT` column, so it should "just work" if
  the template grows a fourth IA block.
- Should CO tag overrides persist across re-uploads of the same course?
  (Design of Phase 4 depends on this.)
- Indirect (CES) attainment currently hard-coded to 85 in the sample — will
  faculty upload a second sheet for this, or type it into the UI?
- **Template evolution:** if faculty push for format changes mid-semester,
  do we version the template (`template_v1`, `v2`) and keep both parsers
  alive, or force a hard cut-over? Initial stance: versioned with a cut-off
  date, documented in `CHANGELOG.md`.
