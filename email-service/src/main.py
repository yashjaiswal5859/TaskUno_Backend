"""
Email Service - Main FastAPI application.
Port: 8005
Runs email consumer in background thread while serving HTTP API.
"""
import sys
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

# Load .env file from email-service directory
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    # Try current directory
    load_dotenv()
    print("⚠️  .env file not found, using environment variables or defaults")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.consumer.email_consumer import EmailWorker
from common.config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="Email Service API",
    docs_url="/docs",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global worker instance
email_worker = None
worker_thread = None

def start_email_worker():
    """Start email worker in background thread."""
    global email_worker
    try:
        email_worker = EmailWorker()
        email_worker.start()
    except Exception as e:
        print(f"❌ Error starting email worker: {str(e)}")
        import traceback
        traceback.print_exc()

@app.on_event("startup")
async def startup_event():
    """Start email worker when FastAPI starts."""
    global worker_thread
    print("=" * 60)
    print("📧 Email Service - Starting...")
    print("=" * 60)
    
    # Display configuration
    print(f"\n📋 Configuration:")
    print(f"   Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"   Queue: {settings.QUEUE_NAME}")
    print(f"   SMTP Host: {settings.SMTP_HOST or 'Not configured'}")
    print(f"   SMTP User: {settings.SMTP_USER or 'Not configured'}")
    print(f"   SMTP Password: {'***' if settings.SMTP_PASSWORD else 'Not configured'}")
    print(f"   From Email: {settings.sender_email or 'Not configured'}")
    print(f"   Port: {settings.PORT}")
    print("=" * 60)
    
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("⚠️  WARNING: SMTP not fully configured. Emails will be logged but not sent.")
        print("   Please configure SMTP_HOST, SMTP_USER, and SMTP_PASSWORD in .env file")
        print("=" * 60)
    
    # Start worker in background thread
    worker_thread = threading.Thread(target=start_email_worker, daemon=True)
    worker_thread.start()
    print("✅ Email worker thread started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop email worker when FastAPI shuts down."""
    global email_worker
    if email_worker:
        email_worker.running = False
        print("👋 Shutting down email worker...")

# Middleware to calculate response time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Service"] = "email-service"
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global email_worker
    
    # Check if worker is running
    worker_status = "running" if (email_worker and email_worker.running) else "stopped"
    
    # Check Redis connection
    from common.cache.redis_client import is_redis_available
    redis_status = "connected" if is_redis_available() else "disconnected"
    
    # Check SMTP configuration
    smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
    
    return {
        "status": "healthy",
        "service": "email-service",
        "port": settings.PORT,
        "worker_status": worker_status,
        "redis_status": redis_status,
        "smtp_configured": smtp_configured,
        "queue_name": settings.QUEUE_NAME
    }

# Status endpoint
@app.get("/status")
async def get_status():
    """Get detailed service status."""
    global email_worker
    
    from common.cache.redis_client import is_redis_available, get_redis_client
    
    worker_status = "running" if (email_worker and email_worker.running) else "stopped"
    redis_status = "connected" if is_redis_available() else "disconnected"
    
    # Get queue length if Redis is available
    queue_length = None
    if is_redis_available():
        try:
            redis_client = get_redis_client()
            queue_length = redis_client.llen(settings.QUEUE_NAME)
        except Exception as e:
            queue_length = f"error: {str(e)}"
    
    return {
        "service": "email-service",
        "port": settings.PORT,
        "worker": {
            "status": worker_status,
            "queue_name": settings.QUEUE_NAME,
            "queue_length": queue_length
        },
        "redis": {
            "status": redis_status,
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT
        },
        "smtp": {
            "configured": bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD),
            "host": settings.SMTP_HOST or "Not configured",
            "port": settings.SMTP_PORT,
            "from_email": settings.sender_email or "Not configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8005"))
    uvicorn.run(
        app,
        host=host,
        port=port
    )
