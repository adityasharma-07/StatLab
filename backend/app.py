"""StatScope API.

A thin FastAPI layer: it finds the right DataFrame, calls the engine, and
returns the engine's dict as typed JSON. There is NO statistics logic here.

Run from the backend/ folder:  uvicorn app:app --reload
Interactive docs:              http://localhost:8000/docs
"""

import io
import os
import uuid
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import engine
from schemas import AnalyzeRequest, AnalyzeResponse, ColumnProfile, DatasetsResponse, UploadResponse

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

# Uploaded CSVs live in memory, keyed by a random session id. No database:
# uploads vanish when the server restarts, which is fine for a demo tool.
# Both limits keep a public deployment from running out of memory.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SESSIONS = 20
uploaded_frames: dict[str, pd.DataFrame] = {}


def get_dataframe(dataset: str | None, session: str | None) -> pd.DataFrame:
    """Find the DataFrame a request is talking about, or raise a clear HTTP error."""
    if dataset is not None:
        if dataset not in engine.list_builtin_datasets():
            raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset}")
        return engine.load_builtin(dataset)
    if session is not None:
        if session not in uploaded_frames:
            raise HTTPException(status_code=404, detail="That upload is no longer available. Please upload the file again.")
        return uploaded_frames[session]
    raise HTTPException(status_code=400, detail="Provide either a 'dataset' name or an upload 'session' id.")


@app.get("/api/datasets", response_model=DatasetsResponse)
def get_datasets():
    return {"datasets": engine.list_builtin_datasets()}


@app.get("/api/columns", response_model=ColumnProfile)
def get_columns(dataset: str | None = None, session: str | None = None):
    df = get_dataframe(dataset, session)
    return engine.profile_columns(df)


@app.post("/api/upload", response_model=UploadResponse)
def post_upload(file: UploadFile):
    contents = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (limit: 5 MB).")

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read that file as a CSV.")
    if len(df) == 0 or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="The CSV needs a header row, at least 2 columns and at least 1 data row.")

    # Dicts remember insertion order, so the first key is the oldest upload.
    if len(uploaded_frames) >= MAX_SESSIONS:
        oldest_session = next(iter(uploaded_frames))
        del uploaded_frames[oldest_session]

    session_id = uuid.uuid4().hex
    uploaded_frames[session_id] = df

    profile = engine.profile_columns(df)
    return {"session_id": session_id, "filename": file.filename or "upload.csv", **profile}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def post_analyze(request: AnalyzeRequest):
    df = get_dataframe(request.dataset, request.session)
    # The engine's dispatcher picks the analysis from the two columns' types.
    return engine.analyze(df, request.col_a, request.col_b)


# In production the built frontend is served from this same server, so the
# frontend can call a relative /api path. Mounted last so it never shadows /api.
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
