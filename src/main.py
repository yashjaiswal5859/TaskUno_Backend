"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uvicorn

# Import all models to ensure relationships are resolved
from src.organization.models import Organization
from src.auth.models import ProductOwner, Developer, User
from src.tasks.models import Task, TaskLog
from src.project.models import Project
from src.notifications.models import EmailQueue

# Import routers
from src.auth.controller.auth_controller import router as auth_router
from src.organization.controller.organization_controller import router as organization_router
from src.tasks.controller.task_controller import router as task_router
from src.project.controller.project_controller import router as project_router
from src.admin.controller.admin_controller import router as admin_router

# Import configuration
from src.config import settings, get_cors_origins

# Create FastAPI app
app = FastAPI(
    title="Scrum Master API",
    docs_url="/docs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(task_router)
app.include_router(project_router)
app.include_router(admin_router)

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
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT
    )

