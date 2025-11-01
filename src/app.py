"""Combined FastAPI application for both Mail Client and Gemini AI services."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path, override=True)

# Import routers from both services
from mail_client_service.api import router as mail_router
from gemini_service.api import router as gemini_router

app = FastAPI(
    title="OSPD Services",
    description="Combined API for Mail Client and Gemini AI Chat services",
    version="0.1.0",
)

# Include both routers with prefixes to avoid conflicts
app.include_router(mail_router, prefix="/mail", tags=["Mail Client"])
app.include_router(gemini_router, prefix="/ai", tags=["Gemini AI"])


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint showing both services are running."""
    return {
        "message": "OSPD Services are running",
        "services": ["Mail Client (/mail)", "Gemini AI (/ai)"],
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "services": ["mail", "ai"]}
