"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered mock trial case simulator with multi-round verdict generation",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🚀 Starting Mock Trial AI...")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")

    # Initialize database tables
    init_db()
    print("✅ Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 Shutting down Mock Trial AI...")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Mock Trial AI - API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"  # TODO: Add actual DB health check
    }


# Import and include API routers
from app.api import auth, cases, documents, verdicts, arguments

app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(cases.router, prefix=f"{settings.API_V1_PREFIX}/cases", tags=["Cases"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/cases", tags=["Documents"])
app.include_router(verdicts.router, prefix=f"{settings.API_V1_PREFIX}/cases", tags=["Verdicts"])
app.include_router(arguments.router, prefix=f"{settings.API_V1_PREFIX}/cases", tags=["Arguments"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
