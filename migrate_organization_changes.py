"""
Migration script to update database schema for organization changes:
1. Remove unique constraint from email in product_owner and developer tables
2. Add organization_id column to developer table
3. Add composite unique constraints (email, organization_id)
4. Update existing Developer records with organization_id from their owner
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import engine
from sqlalchemy import text

def run_migration():
    """Run the migration to update database schema."""
    print("Starting migration...")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Step 1: Check if developer table has organization_id column
            print("\n1. Checking developer table structure...")
            result = conn.execute(text("PRAGMA table_info(developer)"))
            columns = [row[1] for row in result]
            
            if 'organization_id' not in columns:
                print("   Adding organization_id column to developer table...")
                conn.execute(text("""
                    ALTER TABLE developer 
                    ADD COLUMN organization_id INTEGER 
                    REFERENCES organization(id) ON DELETE SET NULL
                """))
                print("   ✓ organization_id column added")
            else:
                print("   ✓ organization_id column already exists")
            
            # Step 2: Update existing Developer records with organization_id from their owner
            print("\n2. Updating existing Developer records with organization_id...")
            conn.execute(text("""
                UPDATE developer
                SET organization_id = (
                    SELECT organization_id 
                    FROM product_owner 
                    WHERE product_owner.id = developer.owner_id
                )
                WHERE organization_id IS NULL AND owner_id IS NOT NULL
            """))
            print("   ✓ Updated Developer records with organization_id from their owners")
            
            # Step 3: For developers without owner, we need to handle them
            # (They should have organization_id set, but if not, we'll leave it NULL for now)
            print("\n3. Checking for developers without organization_id...")
            result = conn.execute(text("""
                SELECT COUNT(*) FROM developer WHERE organization_id IS NULL
            """))
            count = result.scalar()
            if count > 0:
                print(f"   ⚠ Warning: {count} developer(s) without organization_id found")
                print("   These will need to be manually updated or assigned to an organization")
            else:
                print("   ✓ All developers have organization_id")
            
            # Step 4: SQLite doesn't support DROP CONSTRAINT directly
            # We need to recreate the tables without unique constraints
            print("\n4. Recreating tables with new constraints...")
            
            # For product_owner table
            print("   Recreating product_owner table...")
            conn.execute(text("""
                CREATE TABLE product_owner_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50),
                    email VARCHAR(255),
                    "firstName" VARCHAR(50),
                    "lastName" VARCHAR(50),
                    password VARCHAR(255),
                    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE SET NULL,
                    UNIQUE(email, organization_id)
                )
            """))
            
            conn.execute(text("""
                INSERT INTO product_owner_new 
                SELECT id, username, email, "firstName", "lastName", password, organization_id
                FROM product_owner
            """))
            
            conn.execute(text("DROP TABLE product_owner"))
            conn.execute(text("ALTER TABLE product_owner_new RENAME TO product_owner"))
            print("   ✓ product_owner table recreated with composite unique constraint")
            
            # For developer table
            print("   Recreating developer table...")
            conn.execute(text("""
                CREATE TABLE developer_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50),
                    email VARCHAR(255),
                    "firstName" VARCHAR(50),
                    "lastName" VARCHAR(50),
                    password VARCHAR(255),
                    owner_id INTEGER REFERENCES product_owner(id) ON DELETE SET NULL,
                    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE SET NULL,
                    UNIQUE(email, organization_id)
                )
            """))
            
            conn.execute(text("""
                INSERT INTO developer_new 
                SELECT id, username, email, "firstName", "lastName", password, owner_id, organization_id
                FROM developer
            """))
            
            conn.execute(text("DROP TABLE developer"))
            conn.execute(text("ALTER TABLE developer_new RENAME TO developer"))
            print("   ✓ developer table recreated with composite unique constraint")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Organization Schema Migration")
    print("=" * 60)
    print("\nThis migration will:")
    print("  1. Add organization_id to developer table (if missing)")
    print("  2. Update existing developers with organization_id from their owners")
    print("  3. Remove unique constraint from email columns")
    print("  4. Add composite unique constraint (email, organization_id)")
    print("\n⚠️  WARNING: This will recreate the product_owner and developer tables!")
    print("   Make sure you have a backup of your database.")
    print("=" * 60)
    
    # Check if --yes flag is provided
    if '--yes' in sys.argv or '-y' in sys.argv:
        run_migration()
    else:
        try:
            response = input("\nDo you want to continue? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                run_migration()
            else:
                print("Migration cancelled.")
        except EOFError:
            print("\n⚠️  Running in non-interactive mode. Use --yes flag to run automatically.")
            print("   Example: python3 migrate_organization_changes.py --yes")
            sys.exit(1)

