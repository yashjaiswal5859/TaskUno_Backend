"""create all tables with organization

Revision ID: create_all_tables
Revises: 
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'create_all_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organization table
    op.create_table(
        'organization',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create product_owner table
    op.create_table(
        'product_owner',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('firstName', sa.String(length=50), nullable=True),
        sa.Column('lastName', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create developer table
    op.create_table(
        'developer',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('firstName', sa.String(length=50), nullable=True),
        sa.Column('lastName', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['product_owner.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create user table (legacy, for backward compatibility)
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('firstName', sa.String(length=50), nullable=True),
        sa.Column('lastName', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create project table
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('createdDate', sa.DateTime(), nullable=True),
        sa.Column('title', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_type', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['product_owner.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['product_owner.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create task table
    op.create_table(
        'task',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('createdDate', sa.DateTime(), nullable=True),
        sa.Column('dueDate', sa.DateTime(), nullable=True),
        sa.Column('title', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_by_type', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['developer.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['product_owner.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create task_log table
    op.create_table(
        'task_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('createdDate', sa.DateTime(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('old_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create email_queue table
    op.create_table(
        'email_queue',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('to_email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('email_queue')
    op.drop_table('task_log')
    op.drop_table('task')
    op.drop_table('project')
    op.drop_table('user')
    op.drop_table('developer')
    op.drop_table('product_owner')
    op.drop_table('organization')


