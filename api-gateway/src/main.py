"""
API Gateway - Main FastAPI application.
Port: 8000
Routes all requests to appropriate microservices.
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import httpx
import time
import os
import asyncio
from datetime import datetime

from common.middleware.rate_limiter import setup_rate_limiter

# Service URLs from environment variables
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
ORGANIZATION_SERVICE_URL = os.getenv("ORGANIZATION_SERVICE_URL", "http://localhost:8002")
TASKS_SERVICE_URL = os.getenv("TASKS_SERVICE_URL", "http://localhost:8003")
PROJECTS_SERVICE_URL = os.getenv("PROJECTS_SERVICE_URL", "http://localhost:8004")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8005")

# Create FastAPI app
app = FastAPI(
    title="TaskUno API Gateway",
    docs_url="/docs",
    version="1.0.0"
)

# Setup rate limiting
limiter = setup_rate_limiter(app)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service routing map
SERVICE_ROUTES = {
    "/auth": AUTH_SERVICE_URL,
    "/organization": ORGANIZATION_SERVICE_URL,
    "/task": TASKS_SERVICE_URL,
    "/project": PROJECTS_SERVICE_URL,
    "/email": EMAIL_SERVICE_URL,
}


async def proxy_request(
    path: str,
    method: str,
    request: Request,
    service_url: str
) -> Response:
    """Proxy request to appropriate microservice."""
    try:
        # Get request body
        body = await request.body()
        
        # Get headers (exclude host and connection, but preserve Authorization)
        headers = {}
        for key, value in request.headers.items():
            key_lower = key.lower()
            if key_lower not in ["host", "connection", "content-length"]:
                # Preserve original case for Authorization header
                if key_lower == "authorization":
                    headers["Authorization"] = value
                else:
                    headers[key] = value
        
        # Build target URL
        target_url = f"{service_url}{path}"
        
        # Make request to microservice with redirect following enabled
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )
            # Filter out headers that expose internal service information
            filtered_headers = {}
            excluded_headers = {
                "location", "server", "x-forwarded-for", 
                "x-forwarded-host", "x-forwarded-proto"
            }
            
            for key, value in response.headers.items():
                key_lower = key.lower()
                # Skip headers that might expose internal URLs or service info
                if key_lower not in excluded_headers:
                    filtered_headers[key] = value
            
            # Filter out headers that expose internal service information
            filtered_headers = {}
            excluded_headers = {
                "location", "server", "x-forwarded-for", 
                "x-forwarded-host", "x-forwarded-proto"
            }
            
            for key, value in response.headers.items():
                key_lower = key.lower()
                # Skip headers that might expose internal URLs or service info
                if key_lower not in excluded_headers:
                    filtered_headers[key] = value
            
            # Return response with filtered headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=filtered_headers,
                media_type=response.headers.get("content-type")
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Service timeout"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {service_url}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway error: {str(e)}"
        )


def get_service_url(path: str) -> tuple[str, str]:
    """Determine which service to route to based on path."""
    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    # Check each route prefix
    for prefix, service_url in SERVICE_ROUTES.items():
        # Normalize prefix
        prefix_norm = prefix if prefix.startswith("/") else "/" + prefix
        if path.startswith(prefix_norm):
            # Forward the full path to the service (services have prefix in router)
            # So /project becomes /project, /project/123 becomes /project/123
            return service_url, path
    
    # Default to auth service for unknown routes
    return AUTH_SERVICE_URL, path


# Catch-all route for proxying
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def gateway_proxy(path: str, request: Request):
    """Proxy all requests to appropriate microservice."""
    # Health check endpoint
    if path == "health" or path == "":
        return {
            "status": "healthy",
            "service": "api-gateway",
            "port": 8000,
            "routes": {
                "/auth": AUTH_SERVICE_URL,
                "/organization": ORGANIZATION_SERVICE_URL,
                "/task": TASKS_SERVICE_URL,
                "/project": PROJECTS_SERVICE_URL,
                "/email": EMAIL_SERVICE_URL,
            }
        }
    
    # Get service URL and remaining path
    service_url, remaining_path = get_service_url(path)
    
    # Proxy the request
    return await proxy_request(
        remaining_path,
        request.method,
        request,
        service_url
    )


# Middleware to calculate response time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Gateway"] = "api-gateway"
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check all services
    services_status = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in [
            ("auth", AUTH_SERVICE_URL),
            ("organization", ORGANIZATION_SERVICE_URL),
            ("tasks", TASKS_SERVICE_URL),
            ("projects", PROJECTS_SERVICE_URL),
            ("email", EMAIL_SERVICE_URL),
        ]:
            try:
                response = await client.get(f"{url}/health")
                services_status[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": url
                }
            except Exception as e:
                services_status[name] = {
                    "status": "unavailable",
                    "error": str(e),
                    "url": url
                }
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "port": 8000,
        "services": services_status
    }

async def supabase_keep_alive():
    """Background task to keep Supabase awake by calling health API daily."""
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hhbokzrbhxcmuapzwjao.supabase.co")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Wait 1 minute after startup before first call
    await asyncio.sleep(60)
    
    while True:
        try:
            # Call Supabase REST API health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Content-Type": "application/json"
                    }
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Supabase keep-alive: HTTP {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  Supabase keep-alive error: {str(e)}")
        
        # Wait 24 hours (86400 seconds) before next call
        await asyncio.sleep(86400)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    # Start Supabase keep-alive task
    asyncio.create_task(supabase_keep_alive())
    print("✅ Supabase keep-alive task started (will run daily)")

async def supabase_keep_alive():
    """Background task to keep Supabase awake by calling health API daily."""
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hhbokzrbhxcmuapzwjao.supabase.co")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Wait 1 minute after startup before first call
    await asyncio.sleep(60)
    
    while True:
        try:
            # Call Supabase REST API health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Content-Type": "application/json"
                    }
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Supabase keep-alive: HTTP {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  Supabase keep-alive error: {str(e)}")
        
        # Wait 24 hours (86400 seconds) before next call
        await asyncio.sleep(86400)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    # Start Supabase keep-alive task
    asyncio.create_task(supabase_keep_alive())
    print("✅ Supabase keep-alive task started (will run daily)")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host=host,
        port=port
    )

