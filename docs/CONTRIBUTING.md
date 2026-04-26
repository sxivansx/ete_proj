# Contributing to CO Attainment Automation

First off — thank you for considering a contribution. This project replaces
a manual Excel workflow used by a real department; correctness matters more
than velocity, and we're grateful for any help making it better.

The following is a set of guidelines, not rules. Use your best judgment,
and feel free to propose changes to this document in a pull request.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I have a question](#i-have-a-question)
- [How can I contribute?](#how-can-i-contribute)
  - [Reporting bugs](#reporting-bugs)
  - [Suggesting enhancements](#suggesting-enhancements)
  - [Your first code contribution](#your-first-code-contribution)
  - [Improving documentation](#improving-documentation)
- [Development setup](#development-setup)
- [Pull request process](#pull-request-process)
- [Style guides](#style-guides)
  - [Git commit messages](#git-commit-messages)
  - [Python style](#python-style)
  - [TypeScript / React style](#typescript--react-style)
  - [Documentation style](#documentation-style)
- [Touching the calculator or template](#touching-the-calculator-or-template)
- [Security policy](#security-policy)
- [License](#license)
- [Attribution](#attribution)

---

## Code of Conduct

This project and everyone participating in it is governed by a simple
expectation: **be respectful, assume good faith, and focus on the work.**
Harassment, discrimination, or sustained disruption are not tolerated.

By participating, you agree to uphold this expectation. Report unacceptable
behavior to the maintainers privately.

---

## I have a question

> **Before you ask, please search [existing issues](../../issues) and
> [discussions](../../discussions).** Your question may already be answered.

If you still need help:

1. Open a [GitHub Discussion](../../discussions) (preferred) — questions
   live forever and help future contributors.
2. Provide as much context as you can: project version (`git rev-parse HEAD`),
   OS, Python / Bun version, and what you've already tried.
3. Don't open an Issue for a question — Issues are for tracked work.

---

## How can I contribute?

### Reporting bugs

A good bug report is reproducible, isolated, and specific.

**Before submitting:**
- Make sure you're on the latest `main`.
- Run the test suite: `python -m pytest backend/tests -v`.
- Search existing issues — your bug may already be tracked.

**To submit a bug report**, open a GitHub Issue using the **Bug Report**
template and include:

- A clear, descriptive title.
- The exact steps to reproduce — including the workbook (anonymized).
- What you expected to happen vs. what actually happened.
- The CLI / API / UI output you saw (full text, not screenshots, when
  possible).
- Your environment: OS, Python version, browser, commit SHA.
- For numerical bugs: which CO is wrong, what the tool reported, what the
  faculty sheet reported, and the difference.

> **Numerical correctness bugs are P0.** If the calculator produces a
> wrong number, that is treated as a higher-priority issue than crashes
> or layout glitches.

### Suggesting enhancements

Enhancements include new features, additions to existing features, and
non-trivial UX changes.

**Before submitting:**
- Check that it isn't already on the roadmap (`plan.md`) or in an existing
  issue.
- Consider whether it belongs upstream — niche faculty workflows may be
  better as a fork.

**To submit**, open a GitHub Issue using the **Feature Request** template
and include:

- A clear use case: who benefits and why.
- The current workaround (if any) and why it isn't enough.
- A sketch of the proposed change. Mockups or pseudocode are welcome.
- Whether you're willing to implement it yourself.

Significant enhancements should start as a **Discussion**, then graduate to
an Issue once direction is clear.

### Your first code contribution

Unsure where to start? Look for issues labeled:

- [`good first issue`](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
   — beginner-friendly, well-scoped.
- [`help wanted`](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
   — slightly more involved, but still scoped.
- [`docs`](../../issues?q=is%3Aissue+is%3Aopen+label%3Adocs) — perfect for a
   first PR if you're learning the codebase.

Don't open a PR for a non-trivial change without first discussing it on an
Issue. We don't want anyone burning a weekend on a change that won't be
accepted.

### Improving documentation

Documentation lives in:

- `README.md` — top-level pitch and quickstart.
- `CONTRIBUTING.md` — this file.
- `CALCULATIONS.md` — the math behind the calculator.
- `DEPLOY.md` — production deployment notes.
- `plan.md` — phased roadmap and domain derivations.
- Code comments — only where the *why* isn't obvious from the code.

Documentation PRs follow the same process as code PRs but typically merge
faster.

---

## Development setup

You need:

- **Python 3.9+** (the venv on the repo is currently 3.9 — see
  [Python style](#python-style)).
- **[Bun](https://bun.sh)** for the frontend.
- **Docker + Docker Compose** (optional — only for production-shaped runs).

### Clone & install

```bash
git clone https://github.com/<your-fork>/ete-proj.git
cd ete-proj

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
cd frontend && bun install && cd ..
```

### Run the test suite

Always run the suite before opening a PR:

```bash
source .venv/bin/activate
python -m pytest backend/tests -v
```

All tests must pass. Numerical regression tests check parity with the
sample workbook to within `1e-9`.

### Local dev

Two terminals:

```bash
# Terminal 1 — backend on :8000
cd backend
source ../.venv/bin/activate
uvicorn app.api.main:app --reload --port 8000

# Terminal 2 — frontend on :5173
cd frontend
bun run dev
```

Open `http://localhost:5173`, drop the sample workbook
(`backend/samples/python_programming_21ET641.xlsx`) on the uploader.

### Production-shaped run (Docker)

```bash
cp .env.example .env
docker compose up -d --build
```

App runs on `http://localhost:${PORT:-80}`.

---

## Pull request process

1. **Fork** the repo and create a branch from `main`:
   ```
   git checkout -b <type>/<short-description>
   ```
   Examples: `fix/co-tag-parsing`, `feat/po-attainment`, `docs/calc-flow`.

2. **Make small, focused commits.** One commit = one logical change. Don't
   bundle a refactor with a feature. See [Git commit messages](#git-commit-messages).

3. **Add or update tests** for any behavior change. Numerical changes
   *must* include a regression test against a known workbook.

4. **Update documentation:**
   - User-facing changes → `README.md`.
   - Calculator / parser changes → `CALCULATIONS.md`.
   - Template-contract changes → `plan.md` and `CALCULATIONS.md`.

5. **Run pre-flight checks locally:**
   ```bash
   python -m pytest backend/tests -v   # backend
   cd frontend && bun run build         # frontend type-check + bundle
   ```

6. **Open a Pull Request** against `main`. Use the PR template and:
   - Link the Issue it closes (`Closes #123`).
   - Describe **what** changed and **why**.
   - Note any breaking changes prominently.
   - Include before/after screenshots for UI changes.
   - Include before/after numbers for calculator changes.

7. **Address review feedback.** Push follow-up commits — don't force-push
   during review unless asked. We'll squash on merge.

8. **CI must be green.** GitHub Actions runs on every push; a red build
   blocks merging. The `main` branch auto-deploys, so the bar is high.

### Review SLA

Maintainers aim to triage new PRs within 5 business days. Review depth
scales with risk: docs and small fixes are fast; calculator changes get a
thorough read.

---

## Style guides

### Git commit messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/)
shape:

```
<type>(<scope>): <short summary>

<optional longer body, wrapped at ~80 chars>

<optional footer, e.g. "Closes #123" or "BREAKING CHANGE: ...">
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`,
`perf`, `ci`, `build`.

**Examples:**

```
feat(calculator): add PO attainment from CO-PO mapping sheet
fix(parser): treat trailing whitespace in CO tags as a separator
docs(calculations): clarify pooled-mean derivation for IA average
```

Rules:

- Subject in imperative mood ("Add", not "Added" / "Adds").
- Subject ≤ 72 characters.
- Reference Issues / PRs where relevant.
- **Do not** add `Co-Authored-By: Claude` or any AI-tooling co-authors.

### Python style

- Target Python 3.9+. The venv on this repo runs 3.9 — avoid PEP-604 `X | Y`
  unions in **runtime-evaluated** annotations (e.g. FastAPI signatures).
  Module-level annotations are fine because we use
  `from __future__ import annotations`.
- Use `dataclasses` (with `frozen=True` where state is immutable) over
  ad-hoc dicts.
- Pure functions where possible. The calculator is strictly side-effect
  free.
- No `print` in library code. Use the CLI / report module for output.
- Docstrings on public functions, especially in `calculator.py` and
  `parser.py`. Explain the **why**, not the **what**.
- Backend deps stay minimal: `openpyxl`, `pytest`, `fastapi`, `uvicorn`,
  `python-multipart`. Adding pandas / SQLAlchemy / etc. requires
  discussion in an Issue first.

### TypeScript / React style

- Prefer **Bun** over npm / yarn / pnpm: `bun install`, `bun run`, `bunx`.
- Use functional components and React Hooks; no class components.
- Strict TypeScript: no implicit `any`, no `// @ts-ignore` without a
  comment explaining why.
- Match the existing CSS variable conventions in `frontend/src/styles.css`.
- No new UI framework (shadcn / MUI / Chakra) without a dedicated Issue.

### Documentation style

- Markdown, GFM-flavored.
- Hard-wrap prose at ~80 columns for readable diffs.
- Use sentence case in headings ("How it works", not "How It Works").
- Code blocks must specify a language for syntax highlighting.
- Link to source by `file:line` when referencing specific code.

---

## Touching the calculator or template

These are the highest-risk areas in the project. **Read
[`CALCULATIONS.md`](./CALCULATIONS.md) end to end before changing
`backend/app/calculator.py` or `backend/app/parser.py`.**

Specific landmines documented there:

- The per-CO IA average is a **pooled mean** across all IA question
  columns tagged with that CO — *not* a mean of per-IA means. Mean-of-means
  was wrong by ~1% on CO2 / CO3.
- Each CIE question spans **two** Excel columns; row 5 only labels the
  first; row 6 / row 7 carry independent CO tags and max marks.
- Text cells like `"NE"` count as attempted but never as passing.

### Template-contract changes

Changes to the template contract (the layout of the `CIE+SEE` sheet)
require:

1. Bump `TEMPLATE_VERSION` in `backend/app/config.py`.
2. Keep the previous parser working for one release cycle so existing
   uploads don't break.
3. Update `CALCULATIONS.md`, `plan.md`, and the canonical sample workbook.
4. Call out the migration path explicitly in the PR description.

---

## Security policy

If you discover a security vulnerability, **please do not open a public
Issue.** Email the maintainers directly (see commit history for contact)
with:

- A description of the vulnerability.
- Steps to reproduce.
- Affected versions.
- Suggested mitigation, if you have one.

We aim to acknowledge within 72 hours and patch within 14 days for
critical issues.

---

## License

By contributing, you agree that your contributions will be licensed under
the same license as the project. See [`LICENSE`](./LICENSE) for details.

---

## Attribution

This document is loosely modeled on the contribution guides for
[Atom](https://github.com/atom/atom/blob/master/CONTRIBUTING.md),
[Kubernetes](https://github.com/kubernetes/community/blob/master/contributors/guide/README.md),
and [VS Code](https://github.com/microsoft/vscode/blob/main/CONTRIBUTING.md),
adapted for a small academic-tooling project.

Thanks again for contributing — every fix, every doc improvement, every
careful bug report makes this tool more trustworthy for the people who
rely on it.
