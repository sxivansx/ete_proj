# syntax=docker/dockerfile:1.7
# ---------- stage 1: wheels ----------
# Build wheels for all deps in a fat stage, then copy only what we need into
# the slim runtime. Keeps the final image small (no compiler toolchain).
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---------- stage 2: runtime ----------
FROM python:3.11-slim AS runtime

# Run as non-root; uvicorn has no business touching the image's system paths.
RUN useradd --create-home --uid 10001 app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install pre-built wheels from the builder stage.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy just the application code (not tests / samples / scripts).
COPY app ./app

USER app

EXPOSE 8000

# Single-worker uvicorn is fine for a departmental tool; tune later if
# needed. No --reload in the image — that's for local dev.
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
