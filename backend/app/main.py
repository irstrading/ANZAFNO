# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .config import settings
from .api import scanner, stock
from .tasks.celery_app import celery_app
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis/DB, start background tasks
    logger.info("ANZA FNO Platform Starting Up...")
    yield
    # Shutdown: Close connections
    logger.info("ANZA FNO Platform Shutting Down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="India FNO Smart Flow Monitor API",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock Analysis"])

@app.get("/")
def read_root():
    return {"status": "ok", "service": "ANZA FNO Intelligence Platform"}

@app.get("/health")
def health_check():
    # Simple check, could verify Redis/DB connectivity here
    return {"status": "healthy"}
