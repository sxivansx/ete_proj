# CO Attainment Automation

A tool that automates Course Outcome (CO) attainment calculations currently done manually in Excel by the department. Upload a faculty workbook, get instant per-CO attainment results.

**Live:** [https://ete.gitwall.space](https://ete.gitwall.space)

## Features

- Upload faculty CIE+SEE workbooks (.xlsx)
- Auto-detect sheet layout (supports multiple template formats)
- Full sheet view with student marks, pass counts, and per-question CO attainment
- CIE CO-Attainment table (IA average, Assignment, CIE)
- Direct CO-Attainment table (CIE*60% + SEE*40%)
- Green/red color coding against 60% target
- Per-question breakdown with CO tags

## Tech Stack

- **Backend:** Python 3, FastAPI, openpyxl
- **Frontend:** React, TypeScript, Vite
- **Deployment:** Docker Compose, Caddy (auto-HTTPS), DigitalOcean
- **CI/CD:** GitHub Actions (auto-deploy on push to main)

## Local Development

### Backend

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
bun install
bun run dev
```

Open http://localhost:5173 — Vite proxies `/api/*` to the backend.

### Tests

```bash
source .venv/bin/activate
python -m pytest backend/tests -v
```

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

App runs on `http://localhost:80` (or whatever `PORT` is set to in `.env`).

## Project Structure

```
backend/
  app/
    config.py        — thresholds, layout constants
    models.py        — Column, StudentRow, CourseSheet dataclasses
    parser.py        — xlsx parser with auto-layout detection
    calculator.py    — pure attainment math
    api/
      main.py        — FastAPI endpoints
      serializers.py — JSON serialization
  tests/
  samples/           — sample workbook
frontend/
  src/
    components/
      Uploader.tsx         — drag-and-drop xlsx upload
      SheetView.tsx        — full sheet render with summary rows
      AttainmentMatrix.tsx — CIE + Direct CO-Attainment tables
      QuestionTable.tsx    — per-question breakdown
docker-compose.yml
.github/workflows/deploy.yml  — CI/CD
```
