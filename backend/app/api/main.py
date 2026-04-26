"""FastAPI entry point.

Run with::

    uvicorn app.api.main:app --reload --port 8000

from inside ``backend/``.
"""
from __future__ import annotations

import tempfile
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from ..calculator import compute_direct_attainment
from ..config import CalcConfig
from ..parser import load_course_sheet
from ..template import validate as validate_template
from .serializers import serialize_attainment


# Blank template lives next to the sample workbook. ``GET /api/v1/template``
# streams it; ``backend/scripts/build_template.py`` regenerates it from the
# canonical sample.
BLANK_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "samples" / "template_v1.xlsx"
)
TEMPLATE_DOWNLOAD_NAME = "ete_co_attainment_template_v1.xlsx"
XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


app = FastAPI(title="CO Attainment API", version="0.1.0")

# Allow the local Vite dev server + common alt ports to talk to us. In
# production we'll tighten this to the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/template")
def template() -> FileResponse:
    """Serve the blank canonical template so faculty can download-and-fill."""
    if not BLANK_TEMPLATE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Blank template has not been built. Run "
                "`python backend/scripts/build_template.py`."
            ),
        )
    return FileResponse(
        BLANK_TEMPLATE_PATH,
        filename=TEMPLATE_DOWNLOAD_NAME,
        media_type=XLSX_MEDIA_TYPE,
    )


@app.post("/api/v1/upload")
async def upload(
    file: UploadFile = File(...),
    pass_fraction: Optional[float] = None,
    cie_weight: Optional[float] = None,
) -> dict:
    """Accept an .xlsx matching the canonical template, return attainment JSON."""
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Please upload a .xlsx file")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    cfg_kwargs: dict[str, float] = {}
    if pass_fraction is not None:
        cfg_kwargs["pass_fraction"] = pass_fraction
    if cie_weight is not None:
        cfg_kwargs["cie_weight"] = cie_weight

    try:
        cfg = CalcConfig(**cfg_kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Persist to a temp file so openpyxl can stream it. We don't retain the
    # upload here — that's a Phase 4 concern (DB + upload storage).
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)

    try:
        # Run the template validator first. Any non-empty result means the
        # workbook doesn't match the canonical layout — surface every
        # violation so the UI can show the user exactly which cells to fix.
        violations = validate_template(tmp_path)
        if violations:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "template_violations",
                    "message": (
                        f"Workbook does not match the canonical template "
                        f"({len(violations)} issue"
                        f"{'s' if len(violations) != 1 else ''})."
                    ),
                    "violations": [v.to_dict() for v in violations],
                },
            )

        sheet = load_course_sheet(tmp_path)
        result = compute_direct_attainment(sheet, cfg)
    except HTTPException:
        raise
    except ValueError as exc:
        # Parser-level failure that the validator didn't catch — still a
        # template-contract issue from the user's perspective.
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:  # defensive: the parser shouldn't blow up
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    return serialize_attainment(sheet, result)
