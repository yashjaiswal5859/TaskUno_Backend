#!/usr/bin/env python3
"""
Helper script to get DATABASE_URL from Supabase.
You need your database password (not the service role key).
"""

print("=" * 60)
print("How to get DATABASE_URL from Supabase")
print("=" * 60)
print("")
print("Option 1: From Supabase Dashboard (Easiest)")
print("-" * 60)
print("1. Go to: https://supabase.com/dashboard")
print("2. Select your project: hhbokzrbhxcmuapzwjao")
print("3. Go to: Settings > Database")
print("4. Scroll to 'Connection string' section")
print("5. Copy the 'URI' connection string")
print("6. It looks like:")
print("   postgresql://postgres.hhbokzrbhxcmuapzwjao:[YOUR-PASSWORD]@db.hhbokzrbhxcmuapzwjao.supabase.co:5432/postgres")
print("")
print("Option 2: Build it manually")
print("-" * 60)
print("You need your database password (the one you set when creating the project)")
print("")
print("Format:")
print("postgresql://postgres.hhbokzrbhxcmuapzwjao:YOUR_DB_PASSWORD@db.hhbokzrbhxcmuapzwjao.supabase.co:5432/postgres?sslmode=require")
print("")
print("Option 3: Use SUPABASE_DB_PASSWORD in .env")
print("-" * 60)
print("If you know your database password, add this to .env:")
print("SUPABASE_DB_PASSWORD=your-database-password")
print("")
print("Note: Service Role Key ≠ Database Password")
print("  - Service Role Key: For API authentication")
print("  - Database Password: For direct database connection")
print("")
print("=" * 60)


