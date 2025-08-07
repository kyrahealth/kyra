"""merge sources and other migrations

Revision ID: b3c943b424a7
Revises: 8dc1fda384cd, auto_add_sources_to_messages_and_unanswered
Create Date: 2025-07-25 12:53:32.398411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c943b424a7'
down_revision: Union[str, Sequence[str], None] = ('8dc1fda384cd', 'auto_add_sources_to_messages_and_unanswered')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
