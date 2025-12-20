# Dockerfile for AI-Chat Orchestrator Service
FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management (using official image)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace configuration and all source directories
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies (sync only packages needed for orchestrator-service)
RUN uv sync --no-dev --package orchestrator-service

# Expose port 8000
EXPOSE 8000

# Add health check to ensure service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run the service (activate venv and run uvicorn directly)
CMD [".venv/bin/uvicorn", "orchestrator_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
