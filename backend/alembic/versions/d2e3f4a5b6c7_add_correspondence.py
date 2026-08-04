"""Add Correspondence register

A plain log of letters/emails/transmittals the Contractor sends to or
receives from the Engineer. The platform is Contractor-only - the
Engineer never touches it - so this is just a record that an exchange
happened, not a clock: no deadline is computed from it. Evidence gains a
third nullable owner column so a scanned letter can be attached the same
way a photo attaches to an Event or Daily Log.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-04 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'correspondence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('correspondence_no', sa.String(length=50), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('correspondence_date', sa.Date(), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('method', sa.String(length=30), nullable=True),
        sa.Column('related_to', sa.String(length=200), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.add_column(
        'evidence',
        sa.Column('correspondence_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'evidence_correspondence_id_fkey',
        'evidence',
        'correspondence',
        ['correspondence_id'],
        ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('evidence_correspondence_id_fkey', 'evidence', type_='foreignkey')
    op.drop_column('evidence', 'correspondence_id')
    op.drop_table('correspondence')
