from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.main import app as api

app = FastAPI(title="Spam Email Detector")
app.mount("/api", api)
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent / "static"), html=True))
