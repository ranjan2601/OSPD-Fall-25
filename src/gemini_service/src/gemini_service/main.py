from fastapi import FastAPI

from .api import router

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
