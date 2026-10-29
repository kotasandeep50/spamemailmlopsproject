import os
import re
from pathlib import Path


class SpamModel:
    def __init__(self) -> None:
        self.path = Path(os.getenv("MODEL_PATH", "model/artifacts"))
        self.pipeline = None
        self.version = "demo-fallback"
        self._load()

    def _load(self) -> None:
        model_dir = self.path / "classifier"
        if not model_dir.exists():
            return
        try:
            from transformers import pipeline
            self.pipeline = pipeline("text-classification", model=str(model_dir), tokenizer=str(model_dir))
            self.version = "local-distilbert"
        except Exception:
            self.pipeline = None

    @property
    def loaded(self) -> bool:
        return self.pipeline is not None

    def predict(self, text: str) -> tuple[str, float]:
        if self.pipeline:
            result = self.pipeline(text, truncation=True)[0]
            label = "spam" if result["label"].lower() in {"label_1", "spam"} else "ham"
            return label, float(result["score"])

        lowered = text.lower()
        spam_terms = {"win", "prize", "free", "urgent", "claim", "offer", "click", "money"}
        words = set(re.findall(r"\b[\w'-]+\b", lowered))
        matches = len(words & spam_terms)
        if matches >= 2:
            return "spam", min(0.99, 0.55 + matches * 0.08)

        confidence = 0.96 if matches == 0 else 0.72
        legitimate_terms = {"meeting", "project", "regards", "schedule", "review", "please", "thank"}
        if matches == 0 and words & legitimate_terms:
            confidence = 0.99
        return "ham", confidence

    def explain(self, text: str, label: str) -> dict[str, object]:
        lowered = text.lower()
        if label == "spam":
            signals = []
            if any(word in lowered for word in {"urgent", "immediately", "now"}):
                signals.append("Creates urgency or pressure to act")
            if any(word in lowered for word in {"free", "prize", "win", "money", "offer"}):
                signals.append("Uses an unexpected reward or financial promise")
            if any(word in lowered for word in {"click", "claim", "link", "verify"}):
                signals.append("Requests a click, claim, or account verification")
            signals = signals[:3] or ["Message matches suspicious spam patterns"]
            return {
                "verdict": "Likely phishing or scam content",
                "risk_level": "HIGH RISK",
                "summary": "This message contains patterns commonly used to pressure recipients into an unsafe action.",
                "top_signals": signals,
                "recommended_actions": ["Do not click links or reply to this message.", "Verify the request through a known official channel.", "Report or block the sender if it feels unexpected."],
            }
        return {
            "verdict": "Likely legitimate email",
            "risk_level": "LOW RISK",
            "summary": "The message reads like a routine, formal communication without common spam or phishing cues.",
            "top_signals": ["No urgent reward or money language detected", "No suspicious click or verification request detected", "Tone appears consistent with a normal business message"],
            "recommended_actions": ["Review the sender and domain before responding.", "Continue normally if you recognize the context.", "Avoid sharing sensitive information unless independently verified."],
        }
