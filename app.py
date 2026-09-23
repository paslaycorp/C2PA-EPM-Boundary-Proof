from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from boundary.runtime import EPM_RELEASE_COMMIT, run_case

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(
    title="C2PA → EPM Boundary Proof",
    version="0.1-experimental",
    docs_url=None,
    redoc_url=None,
)


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/static/{name}")
def static_file(name: str):
    path = STATIC / name
    if not path.is_file() or path.parent != STATIC:
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/live")
def live():
    return {
        "status": "healthy",
        "service": "c2pa-epm-boundary-proof",
        "epm_release_commit": EPM_RELEASE_COMMIT,
        "normative": False,
        "c2pa_conformance_claim": False,
    }


@app.get("/api/proof/{case_id}")
def proof(case_id: str):
    if case_id not in {"baseline", "purpose-change", "time-change"}:
        raise HTTPException(404, "Unknown proof case")
    try:
        return JSONResponse(run_case(case_id))
    except Exception as exc:
        raise HTTPException(503, f"Boundary proof unavailable: {type(exc).__name__}: {exc}") from exc
