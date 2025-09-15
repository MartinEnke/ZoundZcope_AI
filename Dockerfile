# ---------- Base ----------
FROM python:3.11-slim

# System deps for audio & runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    TZ=UTC \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    UVICORN_WORKERS=1

WORKDIR /app
RUN useradd -ms /bin/bash appuser
RUN mkdir -p /app/backend/uploads

# ---------- Python deps (ONLY prod) ----------
COPY requirements-prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ---------- Copy project ----------
COPY . .
RUN mkdir -p /app/frontend-html/static/analysis && chown -R appuser:appuser /app
USER appuser

# Run from backend/ so your relative paths work
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000
HEALTHCHECK CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["sh","-c","uvicorn --app-dir /app/backend main:app --host 0.0.0.0 --port ${PORT:-8000}"]
