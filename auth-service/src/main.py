"""
Auth Service - Main FastAPI application.
Port: 8001
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from common.config.settings import settings, get_cors_origins
from common.database.db import engine, Base
from common.middleware.rate_limiter import setup_rate_limiter
from common.cache.redis_client import initialize_redis

# Import models to create tables
from src.models import ProductOwner, Developer

# Initialize Redis (for cache invalidation)
initialize_redis()

# Create tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Auth Service API",
    docs_url="/docs",
    version="1.0.0"
)

# Setup rate limiting
limiter = setup_rate_limiter(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from src.controller.auth_controller import router as auth_router
app.include_router(auth_router)

# Middleware to calculate response time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "port": 8001
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=8001
    )

