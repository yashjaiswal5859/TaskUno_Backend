"""
Projects Service - Main FastAPI application.
Port: 8004
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import logging
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s %(levelname)s [%(name)s] %(message)s")
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Initialize New Relic if license key is set (use absolute path to config)
newrelic_config = Path(__file__).parent.parent / 'newrelic.ini'
if os.getenv('NEW_RELIC_LICENSE_KEY') and newrelic_config.exists():
    import newrelic.agent
    newrelic.agent.initialize(str(newrelic_config))

from common.config.settings import settings, get_cors_origins
from common.database.db import engine, Base
from common.middleware.rate_limiter import setup_rate_limiter

# Import models to create tables
from src.models import Project

# Create tables (handle database connection errors gracefully)
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Database connection error: {e}")
    print("⚠️  Service will start but database operations may fail until connection is restored")

# Create FastAPI app
app = FastAPI(
    title="Projects Service API",
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
from src.controller.project_controller import router as project_router
app.include_router(project_router)

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
        "service": "projects-service",
        "port": 8004
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=8004
    )

