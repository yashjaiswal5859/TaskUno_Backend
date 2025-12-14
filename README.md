# TaskUno: Microservices Architecture
## Product Requirements Document & Backend Interview Guide

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Microservices Details](#microservices-details)
4. [Database Architecture](#database-architecture)
5. [Docker Architecture](#docker-architecture)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Deployment Architecture](#deployment-architecture)
8. [Challenges and Solutions](#challenges-and-solutions)
9. [API Endpoints Reference](#api-endpoints-reference)
10. [Backend Interview Questions](#backend-interview-questions)

---

## Executive Summary

TaskUno is a comprehensive task and project management platform built using a microservices architecture. The system enables organizations to manage projects, tasks, teams, and workflows efficiently.

**Key Highlights:**
- 6 microservices with API Gateway pattern
- Docker containerization with custom networking
- CI/CD pipeline with GitHub Actions
- Production deployment on AWS EC2
- HTTPS enabled with Nginx reverse proxy
- Supabase PostgreSQL database with connection pooling

---

## System Architecture

### High-Level Architecture

The TaskUno system follows a microservices architecture pattern with:

1. **API Gateway** - Single entry point for all client requests
2. **Auth Service** - Authentication and authorization
3. **Organization Service** - Organization and team management
4. **Tasks Service** - Task management and tracking
5. **Projects Service** - Project lifecycle management
6. **Email Service** - Asynchronous email notifications

### Technology Stack

**Backend:**
- Framework: FastAPI (Python 3.11)
- Database: Supabase (PostgreSQL)
- Cache/Queue: Redis 7
- Containerization: Docker
- Web Server: Uvicorn (ASGI)
- HTTP Client: httpx (async)

**Infrastructure:**
- Cloud Provider: AWS EC2 (Ubuntu 24.04)
- Reverse Proxy: Nginx
- SSL/TLS: Let's Encrypt
- Domain: task-uno.duckdns.org
- CI/CD: GitHub Actions

**Frontend:**
- Framework: React with TypeScript
- Styling: Tailwind CSS
- HTTP Client: Axios

---

## Microservices Details

### API Gateway (Port 8000)

**Purpose:** Central entry point that routes requests to appropriate microservices.

**Key Features:**
- Request routing based on URL path
- Health check aggregation for all services
- CORS configuration
- Rate limiting
- Request/response transformation
- Error handling and service discovery

**Routing Logic:**
```python
SERVICE_ROUTES = {
    "/auth": AUTH_SERVICE_URL,
    "/organization": ORGANIZATION_SERVICE_URL,
    "/task": TASKS_SERVICE_URL,
    "/project": PROJECTS_SERVICE_URL,
    "/email": EMAIL_SERVICE_URL,
}
```

**Path Forwarding Strategy:**
The gateway forwards the complete path to services. For example, `/organization/` is forwarded as-is to the organization service, which has a router prefix of `/organization`, resulting in the final route `/organization/`.

### Auth Service (Port 8001)

**Purpose:** Handles user authentication, authorization, and user management.

**Key Features:**
- User registration and login
- JWT token generation (access & refresh tokens)
- Token refresh mechanism
- User profile management
- Password hashing (bcrypt)
- Token blacklisting for logout
- User invitation system

**Endpoints:**
- `POST /auth/` - User registration
- `POST /auth/login` - User login
- `GET /auth/profile` - Get user profile
- `PATCH /auth/profile` - Update profile
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (blacklist token)
- `POST /auth/invite` - Invite new user

### Organization Service (Port 8002)

**Purpose:** Manages organizations, teams, developers, and product owners.

**Key Features:**
- Organization CRUD operations
- Developer listing and management
- Product owner management
- Organization chart/hierarchy
- Public organization listing (for registration)

**Endpoints:**
- `GET /organization/` - Get all organizations (public)
- `GET /organization/developers` - Get developers list
- `GET /organization/product-owners` - Get product owners
- `GET /organization/chart` - Get organization chart

### Tasks Service (Port 8003)

**Purpose:** Manages tasks, task assignments, and task logs.

**Key Features:**
- Task CRUD operations
- Task status management (todo, in_progress, done)
- Task priority levels
- Task assignment to users
- Task logging and history
- Task filtering and search

**Endpoints:**
- `GET /task/` - Get all tasks
- `GET /task/{task_id}` - Get task by ID
- `POST /task/` - Create new task
- `PATCH /task/{task_id}` - Update task
- `DELETE /task/{task_id}` - Delete task
- `GET /task/logs` - Get task logs

### Projects Service (Port 8004)

**Purpose:** Manages projects, project lifecycle, and project-related operations.

**Key Features:**
- Project CRUD operations
- Project status tracking
- Project-team associations
- Project timeline management

**Endpoints:**
- `GET /project/` - Get all projects
- `GET /project/{project_id}` - Get project by ID
- `POST /project/` - Create new project
- `PATCH /project/{project_id}` - Update project
- `DELETE /project/{project_id}` - Delete project

### Email Service (Port 8005)

**Purpose:** Handles asynchronous email notifications using Redis queue.

**Key Features:**
- Email queue processing
- SMTP email sending
- Email templates
- Queue management
- Worker-based processing

**Endpoints:**
- `GET /email/health` - Service health check
- `GET /email/status` - Queue and worker status

---

## Database Architecture

### Database: Supabase PostgreSQL

**Connection Strategy:**
- Primary: Direct connection to Supabase
- Production: AWS connection pooler (`aws-1-ap-southeast-1.pooler.supabase.com`)
- Port: 5432 (direct) or 6543 (pooling)
- SSL: Required (`sslmode=require`)

**Connection String Format:**
```
postgresql://postgres.hhbokzrbhxcmuapzwjao:<password>@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require
```

**Key Tables:**
- `users` - User accounts and authentication
- `organizations` - Organization data
- `projects` - Project information
- `tasks` - Task details and status
- `task_logs` - Task history and audit trail

### Redis Cache/Queue

**Purpose:**
- Session caching
- Rate limiting storage
- Email queue backend
- Temporary data storage

**Configuration:**
- Host: `redis` (Docker container name)
- Port: 6379
- Database: 0

---

## Docker Architecture

### Container Strategy

Each microservice runs in its own Docker container with the following structure:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Networking

**Network:** `taskuno-network` (Custom bridge network)

**Network Benefits:**
- Service discovery via container names
- Isolated network for microservices
- Internal communication without exposing ports
- DNS resolution between containers

**Service Communication:**
Services communicate using container names:
- `http://auth-service:8001`
- `http://organization-service:8002`
- `http://tasks-service:8003`
- `http://projects-service:8004`
- `http://email-service:8005`
- `redis://redis:6379`

---

## CI/CD Pipeline

### GitHub Actions Workflow

**Workflow File:** `.github/workflows/deploy.yml`

**Pipeline Stages:**

1. **Build Stage:**
   - Checkout code
   - Set up Docker Buildx
   - Build all Docker images
   - Save images as compressed tar files

2. **Configuration Stage:**
   - Create `.env` file from template
   - Inject secrets from GitHub Secrets
   - Configure service URLs for Docker networking
   - Set Redis host to container name

3. **Deployment Stage:**
   - Transfer files to EC2 via SCP
   - Load Docker images on EC2
   - Stop old containers
   - Start new containers with updated images
   - Clean up temporary files

4. **Infrastructure Stage:**
   - Set up Nginx reverse proxy
   - Configure SSL with Let's Encrypt
   - Set up domain routing

---

## Challenges and Solutions

### Challenge 1: Docker Networking

**Problem:**
Services couldn't communicate using `localhost`. Each container has its own network namespace, so `localhost` refers to the container itself, not other containers.

**Solution:**
1. Created custom Docker network: `taskuno-network`
2. Connected all containers to this network
3. Updated service URLs to use container names:
   - `http://auth-service:8001` instead of `http://localhost:8001`
4. Docker's built-in DNS resolves container names to IP addresses

**Implementation:**
```bash
# Create network
docker network create taskuno-network

# Start container on network
docker run -d --name auth-service \
  --network taskuno-network \
  -p 8001:8001 \
  auth-service:latest
```

### Challenge 2: API Gateway Path Routing

**Problem:**
Gateway was stripping path prefixes before forwarding to services. For example, `/organization/` was being forwarded as `/` to the organization service, causing 404 errors because the service router expects `/organization/`.

**Solution:**
Modified the `get_service_url()` function to forward the complete path instead of stripping the prefix:

```python
def get_service_url(path: str) -> tuple[str, str]:
    for prefix, service_url in SERVICE_ROUTES.items():
        prefix_norm = prefix if prefix.startswith("/") else "/" + prefix
        if path.startswith(prefix_norm):
            # Forward FULL path, don't strip prefix
            return service_url, path
    return AUTH_SERVICE_URL, path
```

**Why This Works:**
Services have router prefixes (e.g., `router = APIRouter(prefix='/organization')`), so when the gateway forwards `/organization/`, the service router adds its prefix, resulting in the correct route `/organization/`.

### Challenge 3: Database Connectivity (IPv6)

**Problem:**
Supabase database hostname `db.hhbokzrbhxcmuapzwjao.supabase.co` resolved only to IPv6 addresses. EC2 instance didn't have IPv6 enabled, causing "Network is unreachable" errors.

**Solution:**
Used AWS connection pooler URL which resolves to IPv4:
```
DATABASE_URL=postgresql://postgres.hhbokzrbhxcmuapzwjao:<password>@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require
```

**Alternative Considered:**
Enabling IPv6 on EC2, but this requires:
- VPC IPv6 CIDR configuration
- Subnet IPv6 CIDR assignment
- EC2 instance IPv6 address assignment
- Security group IPv6 rules

The connection pooler solution was simpler and more efficient.

---

## Backend Interview Questions

### Architecture & Design Questions

#### Q1: Why did you choose microservices architecture over monolithic?

**Answer:**
- **Scalability:** Each service can scale independently based on load
- **Technology Diversity:** Different services can use different tech stacks if needed
- **Fault Isolation:** Failure in one service doesn't bring down the entire system
- **Team Autonomy:** Different teams can work on different services independently
- **Deployment Flexibility:** Services can be deployed independently
- **Resource Optimization:** Only scale services that need more resources

**Trade-offs:**
- Increased complexity in deployment and monitoring
- Network latency between services
- Distributed transaction challenges
- More infrastructure to manage

#### Q2: How does the API Gateway pattern work in your system?

**Answer:**
The API Gateway serves as a single entry point for all client requests:

1. **Routing:** Routes requests to appropriate microservices based on URL path
2. **Aggregation:** Aggregates health checks from all services
3. **Cross-cutting Concerns:**
   - CORS configuration
   - Rate limiting
   - Request/response transformation
   - Error handling
4. **Security:** Centralized authentication validation
5. **Load Balancing:** Can distribute load across service instances

#### Q3: How do services communicate with each other?

**Answer:**
- **Synchronous:** HTTP/REST API calls using `httpx` (async HTTP client)
- **Asynchronous:** Redis-based message queue for email service
- **Service Discovery:** Docker DNS resolves container names to IPs
- **Communication Pattern:**
  - Client → API Gateway → Microservice
  - Microservice → Microservice (via container names)
  - Email Service uses Redis queue for async processing

#### Q4: How did you handle database connections in a microservices architecture?

**Answer:**
- **Database per Service Pattern:** Each service has its own database schema/tables
- **Shared Database:** All services connect to the same Supabase PostgreSQL instance
- **Connection Pooling:** Use AWS connection pooler for better performance
- **Connection String:** Environment variable `DATABASE_URL`
- **ORM:** SQLAlchemy for database operations
- **Migrations:** Alembic for schema migrations (if needed)

### Docker & Containerization Questions

#### Q5: How does Docker networking work in your setup?

**Answer:**
- **Custom Bridge Network:** Created `taskuno-network` for service isolation
- **Service Discovery:** Docker's built-in DNS resolves container names
- **Internal Communication:** Services communicate using container names (e.g., `http://auth-service:8001`)
- **Port Mapping:** External ports mapped to container ports (e.g., `-p 8000:8000`)
- **Network Isolation:** Containers on the same network can communicate without exposing ports externally

**Why Not localhost?**
- Each container has its own network namespace
- `localhost` in a container refers to that container only
- Container names are resolved by Docker DNS to internal IPs
- This enables service discovery without hardcoding IPs

### Security Questions

#### Q6: How is authentication implemented?

**Answer:**
- **JWT Tokens:** Access token (short-lived) and refresh token (long-lived)
- **Token Generation:** Auth service generates tokens using `python-jose`
- **Password Hashing:** bcrypt for secure password storage
- **Token Validation:** Middleware validates JWT on protected routes
- **Token Blacklisting:** Redis stores blacklisted tokens for logout
- **Refresh Mechanism:** Clients use refresh token to get new access tokens

**Flow:**
1. User logs in → Auth service validates credentials
2. Auth service generates JWT tokens
3. Client stores tokens (access + refresh)
4. Client sends access token in `Authorization` header
5. Services validate token using shared secret key
6. On expiry, client uses refresh token to get new access token

### Performance & Scalability Questions

#### Q7: How would you scale this architecture?

**Answer:**

1. **Horizontal Scaling:**
   - Run multiple instances of each service
   - Use load balancer (Nginx) to distribute traffic
   - Stateless services enable easy scaling

2. **Database Scaling:**
   - Use connection pooling (already implemented)
   - Read replicas for read-heavy operations
   - Database sharding if needed

3. **Caching:**
   - Redis for frequently accessed data
   - Cache organization data, user sessions
   - Reduce database load

4. **Async Processing:**
   - Email service already uses async queue
   - Can extend to other background tasks

5. **Container Orchestration:**
   - Migrate to Kubernetes for auto-scaling
   - Use Docker Swarm for simpler orchestration

### CI/CD Questions

#### Q8: How does your CI/CD pipeline work?

**Answer:**

1. **Trigger:** Push to `main/master` branch or manual workflow dispatch
2. **Build Stage:**
   - Checkout code
   - Build Docker images for all services
   - Save images as compressed tar files
3. **Configuration Stage:**
   - Create `.env` from template
   - Inject secrets from GitHub Secrets
   - Configure service URLs for Docker networking
4. **Deployment Stage:**
   - Transfer files to EC2 via SCP
   - Load Docker images
   - Stop old containers
   - Start new containers
5. **Infrastructure Stage:**
   - Set up Nginx (if needed)
   - Configure SSL certificates

**Key Features:**
- Automated deployment on code push
- Zero-downtime deployment (stop old, start new)
- Secret management via GitHub Secrets
- Environment-specific configuration

---

## Conclusion

TaskUno demonstrates a production-ready microservices architecture with:
- Well-structured service separation
- Docker containerization with custom networking
- Automated CI/CD pipeline
- Production deployment with HTTPS
- Database connectivity with connection pooling
- Security best practices
- Scalable architecture design

The challenges faced and solutions implemented provide valuable insights into real-world microservices deployment.

---

## Appendix

### Useful Commands

**Docker Commands:**
```bash
# View running containers
docker ps

# View logs
docker logs <container-name> --tail 50

# Restart container
docker restart <container-name>

# View network
docker network inspect taskuno-network

# Test service connectivity
docker exec api-gateway curl http://auth-service:8001/health
```

**Testing Commands:**
```bash
# Test gateway health
curl https://task-uno.duckdns.org/health

# Test organization endpoint
curl https://task-uno.duckdns.org/organization/

# Test with authentication
curl -H "Authorization: Bearer <token>" \
  https://task-uno.duckdns.org/project/
```

