"""drop daily snapshot

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-08-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('daily_logs', 'daily_snapshot')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'daily_logs', sa.Column('daily_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
