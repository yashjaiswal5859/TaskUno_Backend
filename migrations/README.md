# Database Migration Script

Simple migration script for managing database tables.

## Usage

### Create all tables (up)
```bash
python3 migrate.py up
```

### Drop all tables (down)
```bash
python3 migrate.py down
```

⚠️ **WARNING**: `down` will delete ALL data in the database!

## Tables

The script manages tables for all services:
- `organization`, `product_owner`, `developer`, `user` (Auth Service)
- `task`, `task_log` (Tasks Service)
- `project` (Projects Service)

## Requirements

- Python 3.8+
- `.env` file with `DATABASE_URL` configured
- Shared library accessible

