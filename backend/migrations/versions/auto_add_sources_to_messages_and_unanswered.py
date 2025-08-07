"""add sources to messages and unanswered_queries

Revision ID: auto_add_sources_to_messages_and_unanswered
Revises: 544d534a09ba
Create Date: 2024-07-25 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'auto_add_sources_to_messages_and_unanswered'
down_revision: Union[str, Sequence[str], None] = '544d534a09ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('messages', sa.Column('sources', sa.JSON(), nullable=True))
    op.add_column('unanswered_queries', sa.Column('sources', sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column('messages', 'sources')
    op.drop_column('unanswered_queries', 'sources')
