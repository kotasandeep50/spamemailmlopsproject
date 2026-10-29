import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .model_loader import SpamModel
from .schemas import HealthResponse, PredictionRequest, PredictionResponse

app = FastAPI(title="Spam Email Detection API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
model = SpamModel()
REPORTS_DIR = Path(__file__).resolve().parents[2] / "monitoring" / "reports"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=model.loaded)


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    label, confidence = model.predict(request.text)
    details = model.explain(request.text, label)
    return PredictionResponse(label=label, confidence=round(confidence, 4), model_version=model.version, **details)


@app.get("/monitoring/summary")
def monitoring_summary() -> dict:
    summary_path = REPORTS_DIR / "summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Monitoring report has not been generated")
    return json.loads(summary_path.read_text(encoding="utf-8"))


@app.get("/monitoring/report")
def monitoring_report() -> FileResponse:
    report_path = REPORTS_DIR / "drift_report.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Monitoring report has not been generated")
    return FileResponse(report_path, media_type="text/html")
