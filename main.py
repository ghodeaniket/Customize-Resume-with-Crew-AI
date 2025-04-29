"""Main application entry point."""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, resumes
from app.core.config import settings
from app.core.logging import logger

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Resume Customizer API - Tailor your resume to specific job descriptions",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(resumes.router)


@app.on_event("startup")
async def startup_event():
    """Execute actions on application startup."""
    logger.info("Starting Resume Customizer API")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute actions on application shutdown."""
    logger.info("Shutting down Resume Customizer API")


if __name__ == "__main__":
    """Run the application using uvicorn."""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
