# ─────────────────────────────────────────────────────────
# Zomato AI Recommendation Service – Dockerfile
# ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (none needed for SQLite, but keep layer for future use)
RUN apt-get update && \
    apt-get install -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# ─── Dependencies ────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Application Source ──────────────────────────────────
COPY src/ src/
COPY .env.example .env

# Ensure src is on the Python path
ENV PYTHONPATH="/app/src"

# ─── Non-root user ───────────────────────────────────────
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# ─── Expose & Run ────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "zomato_ai.phase2.api:app", "--host", "0.0.0.0", "--port", "8000"]
