"""Fine-tune DistilBERT and record the run in MLflow."""
import argparse
from pathlib import Path
import pandas as pd
import mlflow
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def compute_metrics(eval_prediction):
    predictions, labels = eval_prediction
    predicted_labels = predictions.argmax(axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predicted_labels, average="binary", zero_division=0)
    return {
        "accuracy": accuracy_score(labels, predicted_labels),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/emails.csv")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()
    data = pd.read_csv(args.data)
    required = {"text", "label"}
    if not required.issubset(data.columns):
        raise ValueError("Dataset must contain text and label columns")
    # SQLite is supported by current MLflow versions; the legacy file store is no longer accepted.
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("spam-email-classification")
    with mlflow.start_run() as run:
        mlflow.log_param("base_model", "distilbert-base-uncased")
        mlflow.log_param("epochs", args.epochs)
        mlflow.log_param("rows", len(data))
        # The full Trainer flow is intentionally isolated here for CPU-friendly review runs.
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
        from datasets import Dataset
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        dataset = Dataset.from_pandas(data[["text", "label"]])
        dataset = dataset.map(lambda row: tokenizer(row["text"], truncation=True, padding="max_length", max_length=128), batched=True)
        split = dataset.train_test_split(test_size=0.2, seed=42)
        model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)
        training_args = TrainingArguments(output_dir="model/artifacts/checkpoints", num_train_epochs=args.epochs, report_to=[])
        trainer = Trainer(model=model, args=training_args, train_dataset=split["train"], eval_dataset=split["test"], compute_metrics=compute_metrics)
        trainer.train()
        metrics = trainer.evaluate()
        mlflow.log_metrics({key: float(value) for key, value in metrics.items() if isinstance(value, (int, float))})
        output = Path("model/artifacts/classifier")
        output.mkdir(parents=True, exist_ok=True)
        trainer.save_model(output)
        tokenizer.save_pretrained(output)
        mlflow.log_artifacts(str(output), artifact_path="classifier")
        print(f"Completed MLflow run {run.info.run_id}")


if __name__ == "__main__":
    main()
