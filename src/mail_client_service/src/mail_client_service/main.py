from fastapi import FastAPI

from .api import router

app = FastAPI()
app.include_router(router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Mail Client Service is running"}
