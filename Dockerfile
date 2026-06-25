# Stage 1: Web UI
FROM node:20-alpine AS web-build
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --silent 2>/dev/null || npm install --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: API + embedded web app
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-san tesseract-ocr-hin tesseract-ocr-mar \
    libgl1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY --from=web-build /web/dist ./frontend/dist

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV APP_MODE=docker

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
