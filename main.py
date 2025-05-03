"""Main application entry point with API versioning."""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router as v1_router
from app.api.middleware.error_handler import ErrorHandlerMiddleware
from app.core.config import settings
from app.core.logging import logger

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Resume Customizer API - Tailor your resume to specific job descriptions",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add custom error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router with version prefix
app.include_router(v1_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {
        "message": "Resume Customizer API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }


@app.on_event("startup")
async def startup_event():
    """Execute actions on application startup."""
    logger.info("Starting Resume Customizer API")
    
    # Validate environment
    from app.core.config import validate_environment
    validation_results = validate_environment()
    
    # Log validation results
    if validation_results["all_validated"]:
        logger.info("Environment validation passed")
    else:
        logger.warning("Environment validation failed - some functionality may be limited")
        
        # Log specific issues
        if not validation_results.get("has_llm_api_key"):
            logger.warning("LLM API key not found - AI customization features will not work")
            logger.warning("Set OPENAI_API_KEY or LLM_API_KEY in the environment or .env file")
        
        if not validation_results.get("uploads_dir_exists"):
            logger.warning("Uploads directory does not exist - document processing may fail")
    
    # Initialize CrewAI environment
    _initialize_crewai_environment()
    
    logger.info(f"API docs available at: /api/docs")
    logger.info(f"API v1 available at: /api/v1")
    

def _initialize_crewai_environment():
    """Initialize CrewAI environment variables."""
    import os
    import sys
    
    # Set environment variables for CrewAI
    os.environ["AGENT_VERBOSE"] = str(settings.AGENT_VERBOSE).lower()
    os.environ["CREW_VERBOSE"] = str(settings.CREW_VERBOSE).lower()
    
    # Forward any API keys to environment
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        logger.debug("Set OPENAI_API_KEY from settings")
    
    if hasattr(settings, 'LLM_API_KEY') and settings.LLM_API_KEY:
        os.environ["LLM_API_KEY"] = settings.LLM_API_KEY
        logger.debug("Set LLM_API_KEY from settings")
    
    if hasattr(settings, 'AGENT_LLM') and settings.AGENT_LLM:
        os.environ["AGENT_LLM"] = settings.AGENT_LLM
        logger.debug(f"Set AGENT_LLM from settings: {settings.AGENT_LLM}")
    
    # Log Python version
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute actions on application shutdown."""
    logger.info("Shutting down Resume Customizer API")


if __name__ == "__main__":
    """Run the application using uvicorn."""
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(settings.PORT) if hasattr(settings, 'PORT') else 8000, 
        reload=settings.DEBUG if hasattr(settings, 'DEBUG') else False
    )
