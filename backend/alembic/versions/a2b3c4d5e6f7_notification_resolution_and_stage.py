"""Alert resolution: notifications gain a stage and a resolved state, and
the run ledger records how many alerts each sweep retired.

Fixes an alert stream that was write-only. Alerts were raised and never
retired, so the bell badge could only ever climb: a PM who submitted
every report they owed still saw the same count as one who had done
nothing, which makes the whole stream worthless within a week.

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-08-01 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Which deadline on the source record an alert is about. Stored as
    # its own column rather than parsed back out of dedupe_key, because
    # it is what identifies an alert for RESOLUTION - raising a fresh
    # alert for a stage, or that deadline being met, retires every
    # earlier live alert on the same (source, stage).
    op.add_column(
        'notifications', sa.Column('stage', sa.String(length=60), nullable=True)
    )

    # "Read" is a human saying they've seen it. "Resolved" is the system
    # saying it no longer applies. Conflating the two is what made the
    # badge monotonic.
    op.add_column(
        'notifications',
        sa.Column(
            'is_resolved',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )
    op.add_column(
        'notifications',
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'notifications',
        sa.Column('resolved_reason', sa.String(length=255), nullable=True),
    )

    op.create_index(op.f('ix_notifications_stage'), 'notifications', ['stage'])
    op.create_index(
        op.f('ix_notifications_is_resolved'), 'notifications', ['is_resolved']
    )

    # Backfill stage for alerts raised before this revision. The old
    # dedupe_key format was "<source_type>:<source_id>:<stage>:<severity>",
    # so the stage is recoverable rather than lost - which matters,
    # because without it those alerts could never be resolved and would
    # sit in the badge forever.
    op.execute(
        """
        UPDATE notifications
        SET stage = NULLIF(split_part(dedupe_key, ':', 3), '')
        WHERE stage IS NULL
        """
    )

    op.add_column(
        'compliance_runs',
        sa.Column(
            'notifications_resolved',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('compliance_runs', 'notifications_resolved')

    op.drop_index(op.f('ix_notifications_is_resolved'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_stage'), table_name='notifications')

    op.drop_column('notifications', 'resolved_reason')
    op.drop_column('notifications', 'resolved_at')
    op.drop_column('notifications', 'is_resolved')
    op.drop_column('notifications', 'stage')
