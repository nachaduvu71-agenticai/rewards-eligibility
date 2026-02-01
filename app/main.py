"""FastAPI application – Legacy Knowledge Extraction Demo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.engine import get_decision_records, run_pipeline
from app.models import PipelineRequest, PipelineResponse, ImmutableDecisionRecord

app = FastAPI(
    title="Legacy Knowledge Extraction Demo",
    description="Explainable AI Decision Pipeline – interactive demo",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text())


@app.post("/api/pipeline", response_model=PipelineResponse)
async def execute_pipeline(req: PipelineRequest):
    return run_pipeline(req)


@app.get("/api/records", response_model=list[ImmutableDecisionRecord])
async def list_records():
    return get_decision_records()
