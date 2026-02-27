from fastapi import FastAPI
from app.core.config import settings
from app.api import scanner

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

app.include_router(scanner.router, prefix=f"{settings.API_PREFIX}/scanner", tags=["Scanner"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}
