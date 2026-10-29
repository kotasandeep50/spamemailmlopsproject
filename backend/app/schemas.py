from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: str = Field(min_length=3, max_length=20_000)


class PredictionResponse(BaseModel):
    label: str
    confidence: float
    model_version: str
    verdict: str
    risk_level: str
    summary: str
    top_signals: list[str]
    recommended_actions: list[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
