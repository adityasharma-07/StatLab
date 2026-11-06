"""FastAPI layer. Resolves the DataFrame, calls the engine, returns JSON.

Run from backend/:  uvicorn app:app --reload
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

app = FastAPI(title="StatLab API", version="1.0.0")

# The Vite dev server is a different origin, so it needs CORS in development.
# Set ALLOWED_ORIGINS to a comma-separated list when deploying.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads are kept in memory, keyed by session id, and lost on restart.
# The limits stop a deployment from filling up.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SESSIONS = 20
uploaded_frames: dict[str, pd.DataFrame] = {}


def get_dataframe(dataset: str | None, session: str | None) -> pd.DataFrame:
    """Resolve a request to a DataFrame, or raise an HTTP error."""
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

    # Dicts keep insertion order, so the first key is the oldest upload.
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
    return engine.analyze(df, request.col_a, request.col_b)


# Serve the built frontend from the same origin so it can call /api relatively.
# Mounted last so it doesn't shadow the API routes.
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
