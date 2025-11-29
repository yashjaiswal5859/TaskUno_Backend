"""Add inviter_id to user table

Revision ID: add_inviter_id
Revises: add_reason_fields
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_inviter_id'
down_revision = 'add_reason_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add inviter_id column to user table
    op.add_column('user', sa.Column('inviter_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_user_inviter',
        'user', 'user',
        ['inviter_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove inviter_id column from user table
    op.drop_constraint('fk_user_inviter', 'user', type_='foreignkey')
    op.drop_column('user', 'inviter_id')


