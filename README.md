# Backend - Fastapi-scrum-master

## Structure

```
backend/
├── src/                    # Source code
│   ├── auth/              # Authentication module
│   │   ├── controller/    # API endpoints
│   │   ├── service/       # Business logic
│   │   ├── validator/     # Validation
│   │   ├── repository/    # Database queries
│   │   ├── models.py
│   │   └── schemas.py
│   ├── tasks/             # Tasks module
│   ├── project/           # Projects module
│   ├── admin/             # Admin module
│   ├── database/          # Database config
│   ├── config/            # Configuration
│   └── main.py            # FastAPI app
├── .env                   # Environment variables
├── scrum_master.db        # SQLite database
├── requirements.txt       # Python dependencies
├── alembic/               # Database migrations
└── alembic.ini            # Alembic config
```

## Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment:
```bash
# Edit .env file with your settings
```

3. Run the server:
```bash
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

## API Documentation

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Configuration

All configuration is in `.env` file:
- Database URL
- JWT secrets
- Server settings
- CORS origins


