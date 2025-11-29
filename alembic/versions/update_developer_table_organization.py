"""Update developer table for organization structure

Revision ID: update_developer_org
Revises: create_all_tables
Create Date: 2024-12-20 12:00:00.000000

This migration ensures:
1. organization_id exists and is NOT NULL in developer table
2. owner_id remains nullable (only used for task assignments, not during registration/invite)
3. Composite unique constraint on (email, organization_id)
4. Removes single email unique constraint
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'update_developer_org'
down_revision = 'create_all_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if organization_id column exists in developer table
    # For SQLite, we need to check differently
    conn = op.get_bind()
    
    # Get table info to check existing columns
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('developer')]
    
    # Step 1: Add organization_id if it doesn't exist
    if 'organization_id' not in columns:
        print("Adding organization_id column to developer table...")
        op.add_column('developer', 
            sa.Column('organization_id', sa.Integer(), nullable=True)
        )
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_developer_organization',
            'developer', 'organization',
            ['organization_id'], ['id'],
            ondelete='SET NULL'
        )
        print("✓ organization_id column added")
    else:
        print("✓ organization_id column already exists")
    
    # Step 2: Update existing developers to have organization_id from their owner (if owner_id exists)
    # This is a data migration for existing records
    print("Updating existing developer records with organization_id...")
    conn.execute(sa.text("""
        UPDATE developer
        SET organization_id = (
            SELECT organization_id 
            FROM product_owner 
            WHERE product_owner.id = developer.owner_id
        )
        WHERE organization_id IS NULL AND owner_id IS NOT NULL
    """))
    print("✓ Updated existing developer records")
    
    # Step 3: Make organization_id NOT NULL (after setting values)
    # For SQLite, we need to recreate the table
    print("Making organization_id NOT NULL...")
    
    # Check database type
    if isinstance(conn.dialect, sqlite.dialect):
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        print("SQLite detected - recreating table with NOT NULL constraint...")
        
        # Create new table with correct structure
        op.create_table(
            'developer_new',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(length=50), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('firstName', sa.String(length=50), nullable=True),
            sa.Column('lastName', sa.String(length=50), nullable=True),
            sa.Column('password', sa.String(length=255), nullable=True),
            sa.Column('owner_id', sa.Integer(), nullable=True),  # Nullable - only for task assignments
            sa.Column('organization_id', sa.Integer(), nullable=False),  # NOT NULL
            sa.ForeignKeyConstraint(['owner_id'], ['product_owner.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email', 'organization_id', name='uq_developer_email_org')
        )
        
        # Copy data
        op.execute("""
            INSERT INTO developer_new 
            (id, username, email, firstName, lastName, password, owner_id, organization_id)
            SELECT id, username, email, firstName, lastName, password, owner_id, 
                   COALESCE(organization_id, (SELECT organization_id FROM product_owner WHERE product_owner.id = developer.owner_id LIMIT 1))
            FROM developer
        """)
        
        # Drop old table and rename new one
        op.drop_table('developer')
        op.rename_table('developer_new', 'developer')
        print("✓ Table recreated with NOT NULL organization_id")
    else:
        # For other databases (PostgreSQL, MySQL), use ALTER COLUMN
        op.alter_column('developer', 'organization_id', nullable=False)
        
        # Drop old unique constraint on email if it exists
        try:
            op.drop_constraint('uq_developer_email', 'developer', type_='unique')
        except:
            pass  # Constraint might not exist
        
        # Add composite unique constraint
        op.create_unique_constraint('uq_developer_email_org', 'developer', ['email', 'organization_id'])
        print("✓ organization_id set to NOT NULL")
    
    # Step 4: Ensure owner_id is nullable (it should already be, but we document it)
    print("✓ owner_id is nullable (used only for task assignments, not registration/invite)")


def downgrade() -> None:
    # Revert changes - make organization_id nullable again
    conn = op.get_bind()
    
    if isinstance(conn.dialect, sqlite.dialect):
        # SQLite - recreate table
        op.create_table(
            'developer_old',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(length=50), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('firstName', sa.String(length=50), nullable=True),
            sa.Column('lastName', sa.String(length=50), nullable=True),
            sa.Column('password', sa.String(length=255), nullable=True),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),  # Nullable again
            sa.ForeignKeyConstraint(['owner_id'], ['product_owner.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email')
        )
        
        op.execute("""
            INSERT INTO developer_old 
            (id, username, email, firstName, lastName, password, owner_id, organization_id)
            SELECT id, username, email, firstName, lastName, password, owner_id, organization_id
            FROM developer
        """)
        
        op.drop_table('developer')
        op.rename_table('developer_old', 'developer')
    else:
        # For other databases
        op.alter_column('developer', 'organization_id', nullable=True)
        op.drop_constraint('uq_developer_email_org', 'developer', type_='unique')
        op.create_unique_constraint('uq_developer_email', 'developer', ['email'])

