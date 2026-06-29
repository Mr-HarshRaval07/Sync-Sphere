from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)


@app.on_event("startup")
def startup_event():
    logger.info("Sync Sphere backend started")


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {
        "message": f"Welcome to {settings.APP_NAME}"
    }


@app.get("/health")
def health():
    logger.info("Health check endpoint called")
    return {
        "status": "healthy"
    }