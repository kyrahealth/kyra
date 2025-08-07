"""add is_admin to users

Revision ID: f3fb93f44df7
Revises: c9636baac678
Create Date: 2025-07-25 11:04:00.580311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3fb93f44df7'
down_revision: Union[str, Sequence[str], None] = 'c9636baac678'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_admin')
