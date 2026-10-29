# Spam Email Detection System

A portable college-project MLOps demo for classifying email as spam or legitimate. The project includes a FastAPI prediction service, React UI, Hugging Face DistilBERT training, MLflow tracking, DVC pipeline metadata, Evidently monitoring, Docker Compose, and GitHub Actions.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Open the frontend with `npm install` and `npm run dev` from `frontend/`. Set `VITE_API_URL=http://localhost:8000` in `frontend/.env` when needed. The API runs in demo mode until a trained model is available.

## Train and track

```powershell
pip install -r model/requirements.txt
python model/train.py --data data/processed/emails.csv --epochs 1
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

The training script accepts a CSV with `text` and `label` columns, logs metrics to MLflow, and saves artifacts to `model/artifacts/`. Use `dvc repro` after configuring a DVC remote.

## Download a real email dataset

The repository includes a four-row fallback dataset for offline startup. To download a small public SpamAssassin email corpus containing ham and spam messages without replacing the fallback data, run:

```powershell
python data/download_spamassassin.py
python pipeline/prepare_data.py
python model/quick_mlflow_baseline.py --data data/raw/spamassassin_emails.csv
```

The downloader writes `data/raw/spamassassin_emails.csv` with `text` and `label` columns. Label `0` is legitimate/ham and label `1` is spam. The original `data/raw/emails.csv` is left unchanged.

## Docker

```powershell
docker compose up --build
```

The API is available at `http://localhost:8000`, the frontend at `http://localhost:5173`, and MLflow at `http://localhost:5000`.

## Monitoring and retraining

```powershell
python monitoring/generate_report.py --reference data/processed/emails.csv --current data/raw/new_emails.csv
python pipeline/retrain_trigger.py --report monitoring/reports/summary.json
```

The report compares email length, word count, link count, and the spam-label rate. Open `monitoring/reports/drift_report.html` directly, or use the application Monitoring page to view the summary and open the Evidently report.

Never commit secrets. Copy `.env.example` to `.env` for local configuration.
