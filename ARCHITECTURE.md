# TaskUno Architecture Diagram

## Mermaid Diagram

```mermaid
graph TB
    subgraph "Clients (Vercel)"
        C1[Client 1<br/>https://taskuno-frontend.vercel.app]
        C2[Client 2<br/>https://taskuno-frontend.vercel.app]
        C3[Client N<br/>Multiple Users]
    end

    subgraph "Internet"
        HTTPS[HTTPS/TLS 1.3<br/>Port 443]
    end

    subgraph "AWS EC2 Instance (Ubuntu 24.04)"
        subgraph "Nginx Reverse Proxy"
            NGINX[Nginx 1.24.0<br/>Port 443 → 8000<br/>SSL Termination<br/>CORS Headers<br/>Rate Limiting]
        end

        subgraph "Docker Network: taskuno-network"
            subgraph "API Gateway Container"
                GATEWAY[API Gateway<br/>Port 8000<br/>FastAPI/Uvicorn<br/>Request Routing<br/>Health Aggregation<br/>CORS Middleware]
            end

            subgraph "Microservices Containers"
                AUTH[Auth Service<br/>Port 8001<br/>FastAPI<br/>JWT Generation<br/>User Management]
                ORG[Organization Service<br/>Port 8002<br/>FastAPI<br/>Org CRUD<br/>Team Management]
                TASKS[Tasks Service<br/>Port 8003<br/>FastAPI<br/>Task CRUD<br/>Task Logs]
                PROJECTS[Projects Service<br/>Port 8004<br/>FastAPI<br/>Project CRUD<br/>Project Management]
                EMAIL[Email Service<br/>Port 8005<br/>FastAPI<br/>Email Queue<br/>SMTP]
            end

            subgraph "Cache & Queue"
                REDIS[Redis Container<br/>Port 6379<br/>Token Blacklist<br/>Rate Limiting<br/>Email Queue]
            end
        end
    end

    subgraph "External Services"
        SUPABASE[(Supabase PostgreSQL<br/>Connection Pooler<br/>Port 5432<br/>SSL Required)]
    end

    %% Client to Nginx
    C1 -->|HTTPS Request<br/>Headers: Origin, Authorization, Content-Type| HTTPS
    C2 -->|HTTPS Request| HTTPS
    C3 -->|HTTPS Request| HTTPS
    HTTPS -->|TLS Encrypted| NGINX

    %% Nginx to Gateway
    NGINX -->|Proxy Pass<br/>http://localhost:8000<br/>Headers: X-Forwarded-For, X-Real-IP| GATEWAY

    %% Gateway to Services
    GATEWAY -->|/auth/*<br/>http://auth-service:8001| AUTH
    GATEWAY -->|/organization/*<br/>http://organization-service:8002| ORG
    GATEWAY -->|/task/*<br/>http://tasks-service:8003| TASKS
    GATEWAY -->|/project/*<br/>http://projects-service:8004| PROJECTS
    GATEWAY -->|/email/*<br/>http://email-service:8005| EMAIL

    %% Services to Redis
    AUTH -->|Token Blacklist<br/>Rate Limiting| REDIS
    ORG -->|Caching| REDIS
    TASKS -->|Caching| REDIS
    PROJECTS -->|Caching| REDIS
    EMAIL -->|Email Queue<br/>Bull Queue| REDIS

    %% Services to Database
    AUTH -->|SQLAlchemy<br/>Connection Pool<br/>pool_size=1, max_overflow=2| SUPABASE
    ORG -->|SQLAlchemy<br/>Connection Pool| SUPABASE
    TASKS -->|SQLAlchemy<br/>Connection Pool| SUPABASE
    PROJECTS -->|SQLAlchemy<br/>Connection Pool| SUPABASE

    %% Styling
    classDef client fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef nginx fill:#ff9800,stroke:#e65100,stroke-width:2px
    classDef gateway fill:#4caf50,stroke:#1b5e20,stroke-width:2px
    classDef service fill:#2196f3,stroke:#0d47a1,stroke-width:2px
    classDef redis fill:#f44336,stroke:#b71c1c,stroke-width:2px
    classDef db fill:#9c27b0,stroke:#4a148c,stroke-width:2px

    class C1,C2,C3 client
    class NGINX nginx
    class GATEWAY gateway
    class AUTH,ORG,TASKS,PROJECTS,EMAIL service
    class REDIS redis
    class SUPABASE db
```

## Request Flow with Headers

### 1. Client Request
```
POST https://task-uno.duckdns.org/auth/login
Headers:
  Origin: https://taskuno-frontend.vercel.app
  Content-Type: application/json
  Accept: application/json
  Authorization: Bearer <token> (if authenticated)
  Cookie: access_token=<token>; refresh_token=<token>
```

### 2. Nginx Processing
```
- Receives HTTPS request on port 443
- Terminates SSL/TLS
- Validates CORS origin
- Applies rate limiting rules
- Adds headers:
  X-Forwarded-For: <client-ip>
  X-Real-IP: <client-ip>
  X-Forwarded-Proto: https
- Proxies to: http://localhost:8000 (API Gateway)
```

### 3. API Gateway Processing
```
- Receives request from Nginx
- Determines target service based on path:
  /auth/* → auth-service:8001
  /organization/* → organization-service:8002
  /task/* → tasks-service:8003
  /project/* → projects-service:8004
  /email/* → email-service:8005
- Forwards full path to service
- Aggregates health checks
- Applies CORS middleware
- Returns response to Nginx
```

### 4. Service Processing (Example: Auth Service)
```
- Receives request from API Gateway
- Validates JWT token (if required)
- Checks Redis for token blacklist
- Queries Supabase database
- Generates new JWT tokens
- Returns response to API Gateway
```

### 5. Response Flow
```
Service → API Gateway → Nginx → Client
Headers:
  Access-Control-Allow-Origin: https://taskuno-frontend.vercel.app
  Access-Control-Allow-Credentials: true
  Content-Type: application/json
  X-Gateway: api-gateway
  X-Process-Time: <ms>
```

## Network Architecture

### Docker Network: taskuno-network
- Type: Bridge network
- Services communicate using container names
- Internal DNS resolution
- Isolated from host network

### Port Mapping
- External: 443 (HTTPS) → Nginx
- Internal Docker: 
  - 8000: API Gateway
  - 8001: Auth Service
  - 8002: Organization Service
  - 8003: Tasks Service
  - 8004: Projects Service
  - 8005: Email Service
  - 6379: Redis

### Security
- HTTPS/TLS encryption (Let's Encrypt)
- CORS protection
- Rate limiting (Nginx + Redis)
- JWT token authentication
- Token blacklisting (Redis)
- SQL injection protection (SQLAlchemy ORM)
- Connection pooling (Supabase)

## Technology Stack

### Frontend (Vercel)
- React + TypeScript
- Axios (HTTP client)
- React Router
- Redux Toolkit

### Backend (EC2)
- FastAPI (Python 3.11)
- Uvicorn (ASGI server)
- Docker + Docker Compose
- Nginx (Reverse proxy)
- Redis (Cache & Queue)

### Database
- Supabase (PostgreSQL)
- Connection pooling
- SSL required

### Infrastructure
- AWS EC2 (Ubuntu 24.04)
- Docker containers
- Nginx reverse proxy
- Let's Encrypt SSL
- GitHub Actions CI/CD







