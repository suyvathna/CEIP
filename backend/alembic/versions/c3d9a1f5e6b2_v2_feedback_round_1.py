"""v2 feedback round 1: project contract fields + status model, event types,
daily diary manpower as text, claim no/governing clause, optional share
link email

Revision ID: c3d9a1f5e6b2
Revises: b2c4d6e8f0a1
Create Date: 2026-07-31 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d9a1f5e6b2'
down_revision: Union[str, Sequence[str], None] = 'b2c4d6e8f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Projects: contract fields + duration-driven completion date ---
    op.add_column('projects', sa.Column('contract_no', sa.String(length=100), nullable=True))
    op.add_column('projects', sa.Column('site_address', sa.String(length=500), nullable=True))
    op.add_column('projects', sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False))
    op.add_column('projects', sa.Column('contract_value', sa.Numeric(18, 2), nullable=True))

    # duration_days is added nullable first and backfilled from each
    # project's existing planned_start/planned_finish gap, then locked to
    # NOT NULL - existing rows have no duration typed in anywhere yet, so a
    # straight nullable=False add would fail against any database that
    # already has project rows.
    op.add_column('projects', sa.Column('duration_days', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE projects
        SET duration_days = GREATEST((planned_finish - planned_start), 0)
        WHERE duration_days IS NULL
        """
    )
    op.alter_column('projects', 'duration_days', nullable=False, server_default='0')

    # --- Daily diaries: manpower becomes free text, not a bare headcount ---
    op.alter_column(
        'daily_diaries',
        'manpower',
        existing_type=sa.Integer(),
        type_=sa.String(length=500),
        postgresql_using='manpower::text',
    )

    # --- Claims: Claim No. + Governing Clause ---
    op.add_column('claims', sa.Column('claim_no', sa.String(length=50), nullable=True))
    op.add_column('claims', sa.Column('governing_clause', sa.String(length=255), nullable=True))
    # Backfill a sequential "CLM-001" style number per project for any
    # claims already in the database, in creation order, so existing
    # claims don't show a blank Claim No. after this migration.
    op.execute(
        """
        WITH numbered AS (
            SELECT id, 'CLM-' || LPAD(
                ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY created_at)::text,
                3, '0'
            ) AS generated_no
            FROM claims
        )
        UPDATE claims
        SET claim_no = numbered.generated_no
        FROM numbered
        WHERE claims.id = numbered.id
          AND claims.claim_no IS NULL
        """
    )

    # --- Claim access tokens: recipient email is optional ---
    op.alter_column(
        'claim_access_tokens',
        'recipient_email',
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'claim_access_tokens',
        'recipient_email',
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.drop_column('claims', 'governing_clause')
    op.drop_column('claims', 'claim_no')

    op.alter_column(
        'daily_diaries',
        'manpower',
        existing_type=sa.String(length=500),
        type_=sa.Integer(),
        postgresql_using='NULLIF(regexp_replace(manpower, \'[^0-9]\', \'\', \'g\'), \'\')::integer',
    )

    op.drop_column('projects', 'duration_days')
    op.drop_column('projects', 'contract_value')
    op.drop_column('projects', 'currency')
    op.drop_column('projects', 'site_address')
    op.drop_column('projects', 'contract_no')
