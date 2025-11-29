"""Create separate ProductOwner and Developer tables

Revision ID: create_separate_tables
Revises: add_inviter_id
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_separate_tables'
down_revision = 'add_inviter_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create product_owner table
    op.create_table(
        'product_owner',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('firstName', sa.String(length=50), nullable=True),
        sa.Column('lastName', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
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
        sa.Column('inviter_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['inviter_id'], ['product_owner.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )


def downgrade() -> None:
    op.drop_table('developer')
    op.drop_table('product_owner')


