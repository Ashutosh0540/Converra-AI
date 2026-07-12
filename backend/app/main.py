from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import app_logger

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI Agent Platform",
)


@app.on_event("startup")
async def startup():

    app_logger.info("Starting Converra AI")


@app.on_event("shutdown")
async def shutdown():

    app_logger.info("Stopping Converra AI")


@app.get("/")
async def root():

    app_logger.info("Root endpoint accessed")

    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "message": "Welcome to Converra AI 🚀",
    }


@app.get("/health")
async def health():

    app_logger.info("Health endpoint checked")

    return {
        "status": "healthy",
        "environment": settings.app_env,
    }