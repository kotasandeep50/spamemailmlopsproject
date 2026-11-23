FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/model/artifacts
WORKDIR /app

COPY deploy/render/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY deploy/render/app_server.py ./app_server.py
COPY monitoring/reports /monitoring/reports
COPY --from=frontend /build/dist ./static
COPY model/artifacts ./model/artifacts

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app /monitoring
USER appuser

EXPOSE 10000
CMD ["sh", "-c", "uvicorn app_server:app --host 0.0.0.0 --port ${PORT:-10000}"]
