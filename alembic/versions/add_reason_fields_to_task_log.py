"""Add reason fields to task log

Revision ID: add_reason_fields
Revises: 982277d032ef
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_reason_fields'
down_revision = '982277d032ef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to task_log table
    op.add_column('task_log', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('task_log', sa.Column('old_status', sa.String(50), nullable=True))
    op.add_column('task_log', sa.Column('new_status', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove columns from task_log table
    op.drop_column('task_log', 'new_status')
    op.drop_column('task_log', 'old_status')
    op.drop_column('task_log', 'reason')


