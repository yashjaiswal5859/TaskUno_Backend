"""
Organization Service - Main FastAPI application.
Port: 8002
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from common.config.settings import settings, get_cors_origins
from common.database.db import engine, Base
from common.middleware.rate_limiter import setup_rate_limiter
from common.cache.redis_client import initialize_redis

# Import models to create tables
from src.models import Organization

# Initialize Redis (for caching)
initialize_redis()

# Create tables (handle database connection errors gracefully)
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Database connection error: {e}")
    print("⚠️  Service will start but database operations may fail until connection is restored")

# Create FastAPI app
app = FastAPI(
    title="Organization Service API",
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
from src.controller.organization_controller import router as organization_router
app.include_router(organization_router)

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
        "service": "organization-service",
        "port": 8002
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=8002
    )

