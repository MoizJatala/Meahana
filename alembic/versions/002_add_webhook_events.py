"""Add webhook_events table and update transcript_chunks

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=True),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('processed', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_id'), 'webhook_events', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_events_meeting_id'), 'webhook_events', ['meeting_id'], unique=False)
    op.create_index(op.f('ix_webhook_events_bot_id'), 'webhook_events', ['bot_id'], unique=False)
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)
    
    # Add confidence column to transcript_chunks
    op.add_column('transcript_chunks', sa.Column('confidence', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove confidence column from transcript_chunks
    op.drop_column('transcript_chunks', 'confidence')
    
    # Drop webhook_events table
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_bot_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_meeting_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_id'), table_name='webhook_events')
    op.drop_table('webhook_events') 