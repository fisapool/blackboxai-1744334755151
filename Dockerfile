# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
     POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev --no-root

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    WORKERS=4 \
    APP_MODULE=app.main:app \
    APP_ENV=production

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/reports /app/data && \
    chown -R appuser:appuser /app

# Copy dependencies from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Security headers
ENV SECURE_HEADERS=1

# Create healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose the port the app runs on
EXPOSE ${PORT}

# Start Gunicorn with proper configuration
CMD gunicorn ${APP_MODULE} \
    --bind 0.0.0.0:${PORT} \
    --workers ${WORKERS} \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --capture-output \
    --enable-stdio-inheritance \
    --graceful-timeout 30
