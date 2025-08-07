"""add confidence_score to messages

Revision ID: fix_add_confidence_score_to_messages
Revises: f3fb93f44df7
Create Date: 2024-07-25 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_add_confidence_score_to_messages'
down_revision: Union[str, Sequence[str], None] = 'f3fb93f44df7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('messages', sa.Column('confidence_score', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('messages', 'confidence_score') 