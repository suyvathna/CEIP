"""normalize legacy Engineer role values - CEIP has no Engineer login role

Revision ID: b2c4d6e8f0a1
Revises: 0c083944653f
Create Date: 2026-07-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2c4d6e8f0a1'
down_revision: Union[str, Sequence[str], None] = '0c083944653f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # CEIP has no Engineer login role at all - an Engineer's only
    # involvement with a claim is a read-only PDF (downloaded by the
    # Contractor, or fetched via a no-account share link - see
    # claim_access_token.py), never a User row. Any account that was
    # registered back when "Engineer" was the default role is normalized
    # here so nothing in the app is left holding a role value it no
    # longer recognizes.
    op.execute("UPDATE users SET role = 'Contractor' WHERE role = 'Engineer'")


def downgrade() -> None:
    """Downgrade schema."""
    # Not reversible - there's no way to tell which 'Contractor' rows
    # used to be 'Engineer' before the upgrade ran.
    pass
