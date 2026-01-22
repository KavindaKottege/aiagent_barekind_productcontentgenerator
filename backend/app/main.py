from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, settings as settings_router

# Create FastAPI application
app = FastAPI(
    title="Product Content Generator API",
    description="AI-powered product content generation for marketing agencies",
    version="1.0.0",
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(settings_router.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Product Content Generator API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}
