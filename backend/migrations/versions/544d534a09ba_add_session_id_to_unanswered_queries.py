"""
add session_id to unanswered_queries

Revision ID: 544d534a09ba
Revises: fix_add_confidence_score_to_messages
Create Date: 2025-07-25 11:58:37.811927
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '544d534a09ba'
down_revision: Union[str, Sequence[str], None] = 'fix_add_confidence_score_to_messages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('unanswered_queries', sa.Column('session_id', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('unanswered_queries', 'session_id')
