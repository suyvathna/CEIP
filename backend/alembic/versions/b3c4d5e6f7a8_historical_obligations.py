"""Mark obligations that fell due before CEIP saw the project as
historical, so they stop generating alerts nobody can act on.

Onboarding a job that had already been running for months back-generates
its register correctly - those obligations really did fall due - but
alerting on each of them individually produced twenty-odd CRITICAL
notices on day one about progress reports that were late months ago,
burying the handful of deadlines that were still live.

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-01 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'compliance_obligations',
        sa.Column(
            'is_historical',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )
    op.create_index(
        op.f('ix_compliance_obligations_is_historical'),
        'compliance_obligations',
        ['is_historical'],
    )

    # Backfill. An obligation whose deadline had already passed when its
    # row was created was history from the moment it existed - created_at
    # is a timestamptz and due_date a date, so the comparison is done in
    # the project timezone the rest of the platform anchors to rather than
    # in whatever timezone the server happens to run in.
    op.execute(
        """
        UPDATE compliance_obligations
        SET is_historical = true
        WHERE due_date < (created_at AT TIME ZONE 'Asia/Phnom_Penh')::date
          AND status IN ('Pending', 'DueSoon', 'Overdue')
        """
    )

    # Retire the individual alerts those obligations already raised. They
    # are what the user was looking at, and they are exactly the noise
    # this revision exists to remove - resolved rather than deleted, so
    # the history of what was warned about survives.
    op.execute(
        """
        UPDATE notifications n
        SET is_resolved = true,
            resolved_at = now(),
            resolved_reason = 'Pre-onboarding history - see the project backlog summary'
        FROM compliance_obligations o
        WHERE n.source_type = 'obligation'
          AND n.source_id = o.id
          AND o.is_historical = true
          AND n.is_resolved = false
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_compliance_obligations_is_historical'),
        table_name='compliance_obligations',
    )
    op.drop_column('compliance_obligations', 'is_historical')
