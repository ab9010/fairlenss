"""
main.py
-------
FastAPI application entrypoint for FairLens.

Run with:
    uvicorn backend.main:app --reload

The API will be available at http://127.0.0.1:8000
Interactive API docs at http://127.0.0.1:8000/docs
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="FairLens API",
    description="Backend for FairLens — an educational AI fairness and bias detection prototype.",
    version="1.0.0",
)

# Allow the static frontend (served from a different port, e.g. Live Server
# or `python -m http.server`) to call this API during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
