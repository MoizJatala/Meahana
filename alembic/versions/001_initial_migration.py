"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create meetings table
    op.create_table(
        'meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_url', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'started', 'failed', 'completed', name='meetingstatus'), nullable=False),
        sa.Column('meeting_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meetings_bot_id'), 'meetings', ['bot_id'], unique=False)
    op.create_index(op.f('ix_meetings_id'), 'meetings', ['id'], unique=False)
    op.create_index(op.f('ix_meetings_meeting_url'), 'meetings', ['meeting_url'], unique=False)
    
    # Create transcript_chunks table
    op.create_table(
        'transcript_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('speaker', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcript_chunks_id'), 'transcript_chunks', ['id'], unique=False)
    
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_transcript_chunks_id'), table_name='transcript_chunks')
    op.drop_table('transcript_chunks')
    op.drop_index(op.f('ix_meetings_meeting_url'), table_name='meetings')
    op.drop_index(op.f('ix_meetings_id'), table_name='meetings')
    op.drop_index(op.f('ix_meetings_bot_id'), table_name='meetings')
    op.drop_table('meetings')
    op.execute('DROP TYPE IF EXISTS meetingstatus') 