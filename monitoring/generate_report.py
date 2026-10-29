"""Generate an Evidently AI data-drift report for the spam-email classifier."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "monitoring" / "reports"
URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an Evidently data-drift report.")
    parser.add_argument("--reference", type=Path, required=True, help="Baseline CSV file")
    parser.add_argument("--current", type=Path, required=True, help="Latest production CSV file")
    return parser.parse_args()


def validate_data(frame: pd.DataFrame, source: Path) -> pd.DataFrame:
    missing_columns = {"text", "label"}.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"{source} is missing required column(s): {', '.join(sorted(missing_columns))}")
    cleaned = frame[["text", "label"]].copy()
    cleaned["text"] = cleaned["text"].fillna("").astype(str)
    cleaned["label"] = pd.to_numeric(cleaned["label"], errors="coerce").fillna(0).astype(int)
    return cleaned


def monitoring_features(frame: pd.DataFrame) -> pd.DataFrame:
    features = frame.copy()
    features["email_length"] = features["text"].str.len()
    features["word_count"] = features["text"].str.split().str.len()
    features["link_count"] = features["text"].str.count(URL_PATTERN)
    features["spam_label"] = (features["label"] == 1).astype(int)
    return features[["email_length", "word_count", "link_count", "spam_label"]]


def build_summary(reference: pd.DataFrame, current: pd.DataFrame) -> dict[str, object]:
    reference_features = monitoring_features(reference)
    current_features = monitoring_features(current)
    reference_length = max(float(reference_features["email_length"].mean()), 1.0)
    text_length_shift = abs(float(reference_features["email_length"].mean()) - float(current_features["email_length"].mean())) / reference_length
    spam_rate_shift = abs(float(reference_features["spam_label"].mean()) - float(current_features["spam_label"].mean()))
    return {
        "drift_detected": bool(text_length_shift > 0.25 or spam_rate_shift > 0.10),
        "text_length_shift": round(text_length_shift, 4),
        "spam_rate_shift": round(spam_rate_shift, 4),
        "reference_rows": int(len(reference)),
        "current_rows": int(len(current)),
        "monitored_columns": ["email_length", "word_count", "link_count", "spam_label"],
        "report_engine": "Evidently AI DataDriftPreset",
        "evidently_report_generated": True,
    }


def create_evidently_report(reference: pd.DataFrame, current: pd.DataFrame, destination: Path) -> None:
    """Use the Evidently 0.7 API pinned in monitoring/requirements.txt."""
    from evidently import Report
    from evidently.presets import DataDriftPreset

    report = Report([DataDriftPreset()])
    snapshot = report.run(reference_data=monitoring_features(reference), current_data=monitoring_features(current))
    snapshot.save_html(str(destination))


def main() -> None:
    args = parse_arguments()
    reference = validate_data(pd.read_csv(args.reference), args.reference)
    current = validate_data(pd.read_csv(args.current), args.current)
    if reference.empty or current.empty:
        raise ValueError("Reference and current datasets must both contain at least one row")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary(reference, current)
    create_evidently_report(reference, current, REPORTS_DIR / "drift_report.html")
    (REPORTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
