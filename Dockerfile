# ---------- Base ----------
FROM python:3.11-slim AS base

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
    TZ=UTC

# app user & dirs
WORKDIR /app
RUN useradd -ms /bin/bash appuser
RUN mkdir -p /app/backend/uploads

# ---------- Python deps (cached) ----------
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy project ----------
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

# Run from backend/ so your relative paths work
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000

HEALTHCHECK CMD curl -fsS http://localhost:8000/ || exit 1

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]

