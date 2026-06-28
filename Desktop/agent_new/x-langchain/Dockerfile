# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Basic build tools (some Python deps may require compilation; safe to keep minimal)
RUN apt-get update \
  && apt-get install -y --no-install-recommends gcc build-essential \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency manifests first (better layer caching)
COPY pyproject.toml uv.lock uv.toml ./

# Create .venv under /app so we can run with container-local env
RUN uv sync --frozen --extra ui

ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the source code
COPY . .

# Logs should be written into /app/logs (mount from host for persistence)
WORKDIR /app

CMD ["python", "src/main.py"]
