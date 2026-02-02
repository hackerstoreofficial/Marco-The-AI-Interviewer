"""
Marco AI Interview Simulator - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from .config import settings
from .database import db
from .routers import candidates, speech, proctoring, interview, evaluation, stt

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered interview simulator with comprehensive feedback",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(candidates.router)
app.include_router(speech.router)
app.include_router(proctoring.router)
app.include_router(interview.router)
app.include_router(evaluation.router)
app.include_router(stt.router)  # Whisper STT endpoint


# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Marco AI Interview Simulator...")
    
    # Connect to database
    await db.connect()
    logger.info("Database connected")
    
    # Initialize upload directory
    settings.UPLOAD_DIR.mkdir(exist_ok=True)
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    
    logger.info("Backend startup complete!")
    
    # Check for critical API keys
    if not any([settings.OPENAI_API_KEY, settings.GEMINI_API_KEY, settings.GROQ_API_KEY, settings.ANTHROPIC_API_KEY]):
        logger.warning("⚠️  No LLM API keys found in environment variables. AI features may not work.")



@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    await db.disconnect()
    logger.info("Database disconnected")


@app.get("/")
async def root():
    """Root endpoint - redirect to static frontend"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "connected" if db._connection else "disconnected"
    }


@app.get("/api/config")
async def get_config():
    """Get public configuration"""
    return {
        "max_upload_size": settings.MAX_UPLOAD_SIZE,
        "allowed_extensions": list(settings.ALLOWED_RESUME_EXTENSIONS),
        "max_questions": settings.MAX_QUESTIONS,
        "interview_duration_minutes": settings.INTERVIEW_DURATION_MINUTES,
        "supported_llm_providers": [
            "openai",
            "gemini",
            "groq",
            "anthropic",
            "openrouter"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
