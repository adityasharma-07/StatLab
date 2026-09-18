"""StatScope API.

A thin FastAPI layer: it finds the right DataFrame, calls the engine, and
returns the engine's dict as typed JSON. There is NO statistics logic here.

Run from the backend/ folder:  uvicorn app:app --reload
Interactive docs:              http://localhost:8000/docs
"""

import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import engine
from schemas import AnalyzeRequest, AnalyzeResponse, ColumnProfile, DatasetsResponse

app = FastAPI(title="StatScope API", version="1.0.0")

# In development the frontend runs on Vite's dev server (a different origin),
# so the browser needs CORS permission to call this API. For a deployed
# frontend, set ALLOWED_ORIGINS to a comma-separated list of its URLs.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_dataframe(dataset: str | None, session: str | None) -> pd.DataFrame:
    """Find the DataFrame a request is talking about, or raise a clear HTTP error."""
    if dataset is not None:
        if dataset not in engine.list_builtin_datasets():
            raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset}")
        return engine.load_builtin(dataset)
    raise HTTPException(status_code=400, detail="Provide a 'dataset' name.")


@app.get("/api/datasets", response_model=DatasetsResponse)
def get_datasets():
    return {"datasets": engine.list_builtin_datasets()}


@app.get("/api/columns", response_model=ColumnProfile)
def get_columns(dataset: str | None = None, session: str | None = None):
    df = get_dataframe(dataset, session)
    return engine.profile_columns(df)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def post_analyze(request: AnalyzeRequest):
    df = get_dataframe(request.dataset, request.session)
    return engine.run_group_comparison(df, value_col=request.col_a, group_col=request.col_b)


# In production the built frontend is served from this same server, so the
# frontend can call a relative /api path. Mounted last so it never shadows /api.
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
