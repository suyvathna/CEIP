"""Drop the Programme (CPM) tables

The Programme tab (activities, predecessor links, and event-to-activity
delay impacts) is removed from the platform - the Contractor found the
critical-path scheduling feature out of scope for a records/claims tool,
and its one cross-reference into Claims (the delay-analysis panel) has
been removed from ClaimDetailPage accordingly. Reversible: downgrade()
recreates the three tables exactly as 0c083944653f first created them,
empty.

Revision ID: c1d2e3f4a5b6
Revises: b3c4d5e6f7a8
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table('event_activity_impacts')
    op.drop_table('activity_predecessors')
    op.drop_table('activities')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'activities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('activity_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('planned_start', sa.Date(), nullable=False),
        sa.Column('planned_finish', sa.Date(), nullable=False),
        sa.Column('actual_start', sa.Date(), nullable=True),
        sa.Column('actual_finish', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'activity_predecessors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('activity_id', sa.UUID(), nullable=False),
        sa.Column('predecessor_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
        sa.ForeignKeyConstraint(['predecessor_id'], ['activities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'event_activity_impacts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('activity_id', sa.UUID(), nullable=False),
        sa.Column('impact_days', sa.Integer(), nullable=False),
        sa.Column('risk_category', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
