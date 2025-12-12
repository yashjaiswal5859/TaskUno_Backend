"""
Migration script to remove username column from product_owner and developer tables.
Run this script after updating the models to remove username field.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def get_database_url():
    """Get database URL from environment variables."""
    # Try DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return database_url
    
    # Try building from Supabase environment variables
    supabase_url = os.getenv('SUPABASE_URL', 'https://hhbokzrbhxcmuapzwjao.supabase.co')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    if db_password:
        # Extract project reference from Supabase URL
        if supabase_url.startswith('https://'):
            project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '').strip()
            # Supabase connection string format
            return f"postgresql://postgres.{project_ref}:{db_password}@db.{project_ref}.supabase.co:5432/postgres?sslmode=require"
    
    return None

def remove_username_columns():
    """Remove username column from product_owner and developer tables."""
    database_url = get_database_url()
    
    if not database_url:
        print("❌ Error: Database URL not found.")
        print("Please set DATABASE_URL environment variable or SUPABASE_DB_PASSWORD")
        print("Example: export DATABASE_URL='postgresql://...'")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if username column exists in product_owner table
                check_po = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'product_owner' 
                    AND column_name = 'username'
                """)
                result_po = conn.execute(check_po).fetchone()
                
                if result_po:
                    print("📝 Removing username column from product_owner table...")
                    drop_po = text("ALTER TABLE product_owner DROP COLUMN IF EXISTS username")
                    conn.execute(drop_po)
                    print("✅ Removed username column from product_owner table")
                else:
                    print("ℹ️  username column does not exist in product_owner table")
                
                # Check if username column exists in developer table
                check_dev = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'developer' 
                    AND column_name = 'username'
                """)
                result_dev = conn.execute(check_dev).fetchone()
                
                if result_dev:
                    print("📝 Removing username column from developer table...")
                    drop_dev = text("ALTER TABLE developer DROP COLUMN IF EXISTS username")
                    conn.execute(drop_dev)
                    print("✅ Removed username column from developer table")
                else:
                    print("ℹ️  username column does not exist in developer table")
                
                # Commit transaction
                trans.commit()
                print("\n✅ Migration completed successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during migration: {str(e)}")
                return False
                
    except OperationalError as e:
        print(f"❌ Database connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting migration to remove username columns...\n")
    success = remove_username_columns()
    sys.exit(0 if success else 1)

