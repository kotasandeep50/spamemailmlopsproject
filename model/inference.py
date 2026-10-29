from pathlib import Path
from transformers import pipeline


def load_classifier(path: str = "model/artifacts/classifier"):
    model_path = Path(path)
    if not model_path.exists():
        raise FileNotFoundError(f"No trained model at {model_path}")
    return pipeline("text-classification", model=str(model_path), tokenizer=str(model_path))


def predict(text: str, classifier=None) -> dict[str, float | str]:
    classifier = classifier or load_classifier()
    result = classifier(text, truncation=True)[0]
    return {"label": result["label"], "confidence": float(result["score"])}
