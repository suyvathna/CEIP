"""v2 feedback round 2: event_no, claim governing/cost fields, claim
daily-log and evidence links

Revision ID: e4f5a6b7c8d9
Revises: d1e2f3a4b5c6
Create Date: 2026-08-01 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Events: Event No. (mirrors Claim.claim_no) ---
    op.add_column('events', sa.Column('event_no', sa.String(length=50), nullable=True))
    # Backfill a sequential "EVT-001" style number per project for any
    # events already in the database, in creation order, so existing
    # events don't show a blank Event No. after this migration.
    op.execute(
        """
        WITH numbered AS (
            SELECT id, 'EVT-' || LPAD(
                ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY created_at)::text,
                3, '0'
            ) AS generated_no
            FROM events
        )
        UPDATE events
        SET event_no = numbered.generated_no
        FROM numbered
        WHERE events.id = numbered.id
          AND events.event_no IS NULL
        """
    )

    # --- Claims: claim_basis (the EventType-keyed reason driving the
    # governing-clause dropdown) + claimed/awarded cost fields ---
    op.add_column('claims', sa.Column('claim_basis', sa.String(length=100), nullable=True))
    op.add_column('claims', sa.Column('claimed_cost_amount', sa.Numeric(18, 2), nullable=True))
    op.add_column(
        'claim_responses',
        sa.Column('cost_awarded_amount', sa.Numeric(18, 2), nullable=True),
    )

    # --- Claims: link to Daily Logs and Evidence, mirroring claim_events ---
    op.create_table(
        'claim_daily_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        'claim_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('claim_evidence')
    op.drop_table('claim_daily_logs')

    op.drop_column('claim_responses', 'cost_awarded_amount')
    op.drop_column('claims', 'claimed_cost_amount')
    op.drop_column('claims', 'claim_basis')

    op.drop_column('events', 'event_no')
