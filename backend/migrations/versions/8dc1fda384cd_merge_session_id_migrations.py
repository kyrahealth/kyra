"""merge session_id migrations

Revision ID: 8dc1fda384cd
Revises: 544d534a09ba, auto_add_session_id_to_unanswered_queries
Create Date: 2025-07-25 12:02:09.888969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dc1fda384cd'
down_revision: Union[str, Sequence[str], None] = ('544d534a09ba', 'auto_add_session_id_to_unanswered_queries')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
