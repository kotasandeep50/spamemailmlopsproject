"""Fast, transparent baseline experiment for the college MLOps review."""
import argparse
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/emails.csv")
    args = parser.parse_args()

    data = pd.read_csv(args.data).dropna(subset=["text", "label"])
    if not {"text", "label"}.issubset(data.columns):
        raise ValueError("Dataset must contain text and label columns")
    if data["label"].nunique() < 2:
        raise ValueError("Dataset must contain both spam and legitimate labels")

    texts = data["text"].astype(str)
    labels = data["label"].astype(int)
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=0.5, random_state=42, stratify=labels
    )
    classifier = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("spam-email-baseline")
    with mlflow.start_run(run_name="tfidf-logistic-regression") as run:
        dataset_source = mlflow.data.from_pandas(data, source=str(Path(args.data).resolve()), name="spamassassin-emails")
        mlflow.log_input(dataset_source, context="training")
        classifier.fit(train_texts, train_labels)
        predictions = classifier.predict(test_texts)
        precision, recall, f1, _ = precision_recall_fscore_support(
            test_labels, predictions, average="binary", zero_division=0
        )
        metrics = {
            "accuracy": accuracy_score(test_labels, predictions),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
        mlflow.log_params({"model": "tfidf-logistic-regression", "train_rows": len(train_texts), "test_rows": len(test_texts)})
        mlflow.log_metrics({name: float(value) for name, value in metrics.items()})
        artifact_path = Path("model/artifacts/baseline")
        artifact_path.mkdir(parents=True, exist_ok=True)
        mlflow.sklearn.log_model(classifier, "model")
        print(f"Completed MLflow run: {run.info.run_id}")
        print("Metrics:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.4f}")


if __name__ == "__main__":
    main()
