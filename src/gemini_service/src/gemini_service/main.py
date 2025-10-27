from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from .api import router

# Load environment variables from .env file
# Go up from: gemini_service/main.py -> gemini_service/ -> src/ -> src/ -> hw1/
env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

app = FastAPI(
    title="Gemini AI Service",
    description="FastAPI service providing AI chat capabilities using Google Gemini",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Gemini AI Service is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
