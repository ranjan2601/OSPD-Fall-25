# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy source code
COPY src/ ./src/
COPY main.py ./

# Install dependencies including workspace members and dev extras (httpx needed for generated client)
RUN uv sync --frozen --all-packages --extra dev

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run the FastAPI service
CMD ["uv", "run", "uvicorn", "src.mail_client_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
