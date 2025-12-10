#!/usr/bin/env python3
"""
Check and validate .env file for migrations.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv not installed. Install with: pip install python-dotenv")
    exit(1)

migrations_dir = Path(__file__).parent
env_file = migrations_dir / ".env"

print("🔍 Checking .env file...")
print(f"   Location: {env_file.absolute()}")
print("")

if not env_file.exists():
    print("❌ .env file not found!")
    print("")
    print("Create a .env file with the following required fields:")
    print("  - DATABASE_URL (or SUPABASE_URL + SUPABASE_DB_PASSWORD)")
    print("  - SECRET_KEY")
    print("  - REFRESH_SECRET_KEY")
    exit(1)

# Load .env file
load_dotenv(env_file)

print("📋 Environment Variables:")
print("-" * 60)

required_vars = {
    "DATABASE_URL": "Database connection string",
    "SECRET_KEY": "JWT secret key",
    "REFRESH_SECRET_KEY": "JWT refresh secret key"
}

optional_vars = {
    "SUPABASE_URL": "Supabase URL (if not using DATABASE_URL)",
    "SUPABASE_DB_PASSWORD": "Supabase database password",
    "ALGORITHM": "JWT algorithm (default: HS256)",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "Access token expiry (default: 30)",
    "REFRESH_TOKEN_EXPIRE_DAYS": "Refresh token expiry (default: 7)",
}

missing = []
has_database = False

# Check required variables
for var, desc in required_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "SECRET" in var or "KEY" in var or "PASSWORD" in var or "URL" in var:
            display_value = value[:20] + "..." if len(value) > 20 else "***"
        else:
            display_value = value
        print(f"✅ {var:<25} = {display_value}")
        if var == "DATABASE_URL":
            has_database = True
    else:
        print(f"❌ {var:<25} = NOT SET")
        missing.append(var)

# Check if SUPABASE_URL is set (alternative to DATABASE_URL)
if not has_database:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_password = os.getenv("SUPABASE_DB_PASSWORD")
    if supabase_url and supabase_password:
        print(f"✅ SUPABASE_URL{'':<18} = {supabase_url[:30]}...")
        print(f"✅ SUPABASE_DB_PASSWORD{'':<8} = ***")
        has_database = True
        if "DATABASE_URL" in missing:
            missing.remove("DATABASE_URL")

print("")
print("📋 Optional Variables:")
print("-" * 60)

for var, desc in optional_vars.items():
    value = os.getenv(var)
    if value:
        display_value = value[:30] + "..." if len(value) > 30 else value
        print(f"ℹ️  {var:<25} = {display_value}")
    else:
        print(f"⚪ {var:<25} = (not set, using default)")

print("")
print("=" * 60)

if missing:
    print("❌ Missing required variables:")
    for var in missing:
        print(f"   - {var}")
    print("")
    print("Add these to your .env file:")
    print("")
    if "DATABASE_URL" in missing:
        print("DATABASE_URL=postgresql://postgres.your-project-ref:password@db.your-project-ref.supabase.co:5432/postgres?sslmode=require")
    if "SECRET_KEY" in missing:
        print("SECRET_KEY=your-jwt-secret-key-change-in-production")
    if "REFRESH_SECRET_KEY" in missing:
        print("REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production")
    print("")
    exit(1)
else:
    print("✅ All required variables are set!")
    print("")
    print("You can now run migrations:")
    print("  python3 migrate.py up    # Create tables")
    print("  python3 migrate.py down  # Drop tables")
    exit(0)


