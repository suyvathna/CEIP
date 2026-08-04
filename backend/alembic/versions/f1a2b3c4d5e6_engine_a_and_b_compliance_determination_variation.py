"""Engine A (compliance scheduler) and Engine B (contractual state
machine): compliance obligations, run ledger, notifications,
Sub-Clause 3.7 determinations, Clause 13 / Sub-Clause 3.5 variations,
plus the contract milestones and periods both engines measure from.

Revision ID: f1a2b3c4d5e6
Revises: e4f5a6b7c8d9
Create Date: 2026-08-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ------------------------------------------------------------------
    # Projects: contract edition, milestones, and the engines' periods
    # ------------------------------------------------------------------
    # Every one of these is added with a server_default so existing rows
    # get a sensible value without a separate backfill, and every
    # milestone date is nullable because it may genuinely not have
    # happened yet - Engine A skips obligations anchored on a missing
    # milestone rather than inventing a date for them.
    op.add_column(
        'projects',
        sa.Column(
            'contract_edition',
            sa.String(length=20),
            nullable=False,
            server_default='FIDIC 2017',
        ),
    )
    op.add_column(
        'projects', sa.Column('letter_of_acceptance_date', sa.Date(), nullable=True)
    )
    op.add_column(
        'projects', sa.Column('taking_over_date', sa.Date(), nullable=True)
    )
    op.add_column(
        'projects',
        sa.Column('performance_certificate_date', sa.Date(), nullable=True),
    )
    op.add_column(
        'projects',
        sa.Column(
            'defects_notification_period_days',
            sa.Integer(),
            nullable=False,
            server_default='365',
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'progress_report_due_days',
            sa.Integer(),
            nullable=False,
            server_default='7',
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'statement_due_days', sa.Integer(), nullable=False, server_default='7'
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'engineer_determination_period_days',
            sa.Integer(),
            nullable=False,
            server_default='42',
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'nod_period_days', sa.Integer(), nullable=False, server_default='28'
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'deemed_variation_notice_days',
            sa.Integer(),
            nullable=False,
            server_default='7',
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'variation_proposal_period_days',
            sa.Integer(),
            nullable=False,
            server_default='28',
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'compliance_alert_lead_days',
            sa.Integer(),
            nullable=False,
            server_default='7',
        ),
    )

    # ------------------------------------------------------------------
    # Engine A: the compliance register
    # ------------------------------------------------------------------
    op.create_table(
        'compliance_obligations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_key', sa.String(length=80), nullable=False),
        sa.Column('period_key', sa.String(length=20), nullable=False),
        sa.Column('clause_code', sa.String(length=40), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('owed_by', sa.String(length=20), nullable=False),
        sa.Column('anchor_date', sa.Date(), nullable=True),
        sa.Column(
            'offset_days', sa.Integer(), nullable=False, server_default='0'
        ),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column(
            'status', sa.String(length=30), nullable=False, server_default='Pending'
        ),
        sa.Column(
            'rights_destroying',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        sa.Column('submitted_date', sa.Date(), nullable=True),
        sa.Column('submitted_reference', sa.String(length=120), nullable=True),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('waived_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        # The idempotency guarantee the whole scheduler rests on: the
        # sweep can run any number of times a day and produce the same
        # rows.
        sa.UniqueConstraint(
            'project_id',
            'rule_key',
            'period_key',
            name='uq_compliance_obligation_project_rule_period',
        ),
    )
    op.create_index(
        op.f('ix_compliance_obligations_project_id'),
        'compliance_obligations',
        ['project_id'],
    )
    op.create_index(
        op.f('ix_compliance_obligations_due_date'),
        'compliance_obligations',
        ['due_date'],
    )
    op.create_index(
        op.f('ix_compliance_obligations_status'),
        'compliance_obligations',
        ['status'],
    )

    # ------------------------------------------------------------------
    # Engine A: the sweep's own audit trail
    # ------------------------------------------------------------------
    op.create_table(
        'compliance_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_date', sa.Date(), nullable=False),
        sa.Column(
            'trigger_source',
            sa.String(length=20),
            nullable=False,
            server_default='scheduled',
        ),
        sa.Column(
            'status', sa.String(length=20), nullable=False, server_default='running'
        ),
        sa.Column(
            'projects_processed', sa.Integer(), nullable=False, server_default='0'
        ),
        sa.Column(
            'obligations_created', sa.Integer(), nullable=False, server_default='0'
        ),
        sa.Column(
            'obligations_updated', sa.Integer(), nullable=False, server_default='0'
        ),
        sa.Column(
            'notifications_created', sa.Integer(), nullable=False, server_default='0'
        ),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_compliance_runs_run_date'), 'compliance_runs', ['run_date']
    )

    # ------------------------------------------------------------------
    # Engine B: Sub-Clause 3.7 determinations
    # ------------------------------------------------------------------
    op.create_table(
        'determinations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Nullable: Sub-Clause 3.7 governs "any matter or Claim", and a
        # valuation or measurement dispute that never became a 20.2 Claim
        # still opens a Notice of Dissatisfaction window.
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('determination_no', sa.String(length=50), nullable=True),
        sa.Column('matter_title', sa.String(length=255), nullable=False),
        sa.Column('matter_description', sa.Text(), nullable=True),
        sa.Column('subject_clause', sa.String(length=255), nullable=True),
        sa.Column('referred_date', sa.Date(), nullable=False),
        sa.Column('agreement_reached_date', sa.Date(), nullable=True),
        sa.Column('determination_notice_date', sa.Date(), nullable=True),
        # The 28-day NOD clock runs from THIS, not from the date printed
        # on the Engineer's letter.
        sa.Column('determination_received_date', sa.Date(), nullable=True),
        sa.Column('determination_summary', sa.Text(), nullable=True),
        sa.Column(
            'outcome',
            sa.String(length=30),
            nullable=False,
            server_default='NotYetDetermined',
        ),
        sa.Column('days_determined', sa.Integer(), nullable=True),
        sa.Column('cost_determined', sa.Numeric(18, 2), nullable=True),
        sa.Column(
            'determination_evidence_id', postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column('nod_given_date', sa.Date(), nullable=True),
        sa.Column('nod_reference', sa.String(length=120), nullable=True),
        sa.Column('nod_grounds', sa.Text(), nullable=True),
        sa.Column('nod_evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'is_final_and_binding',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        sa.Column('became_final_on', sa.Date(), nullable=True),
        sa.Column(
            'status',
            sa.String(length=30),
            nullable=False,
            server_default='UnderConsultation',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id']),
        sa.ForeignKeyConstraint(
            ['determination_evidence_id'], ['evidence.id']
        ),
        sa.ForeignKeyConstraint(['nod_evidence_id'], ['evidence.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_determinations_project_id'), 'determinations', ['project_id']
    )
    op.create_index(
        op.f('ix_determinations_claim_id'), 'determinations', ['claim_id']
    )
    op.create_index(op.f('ix_determinations_status'), 'determinations', ['status'])

    # ------------------------------------------------------------------
    # Engine B: Clause 13 Variations and Sub-Clause 3.5 instructions
    # ------------------------------------------------------------------
    op.create_table(
        'variations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variation_no', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('origin', sa.String(length=30), nullable=False),
        sa.Column(
            'status', sa.String(length=30), nullable=False, server_default='Logged'
        ),
        sa.Column('instruction_reference', sa.String(length=120), nullable=True),
        sa.Column('instruction_date', sa.Date(), nullable=True),
        sa.Column('instruction_received_date', sa.Date(), nullable=True),
        # False is the alarm condition: an instruction that changes the
        # Works but never used the word "Variation".
        sa.Column(
            'is_labelled_as_variation',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        sa.Column(
            'work_commenced',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        sa.Column('work_commenced_date', sa.Date(), nullable=True),
        sa.Column('notice_given_date', sa.Date(), nullable=True),
        sa.Column('notice_reference', sa.String(length=120), nullable=True),
        sa.Column('notice_evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('proposal_requested_date', sa.Date(), nullable=True),
        sa.Column('proposal_submitted_date', sa.Date(), nullable=True),
        sa.Column('quoted_days', sa.Integer(), nullable=True),
        sa.Column('quoted_cost', sa.Numeric(18, 2), nullable=True),
        sa.Column('agreed_days', sa.Integer(), nullable=True),
        sa.Column('agreed_cost', sa.Numeric(18, 2), nullable=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.ForeignKeyConstraint(['notice_evidence_id'], ['evidence.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_variations_project_id'), 'variations', ['project_id'])
    op.create_index(op.f('ix_variations_status'), 'variations', ['status'])

    # ------------------------------------------------------------------
    # Shared: the alert stream both engines write into
    # ------------------------------------------------------------------
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('clause_code', sa.String(length=40), nullable=True),
        # Free text, not an FK: an alert must survive the deletion of
        # whatever raised it. An alert history that silently loses rows
        # is not a history.
        sa.Column('source_type', sa.String(length=30), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('link_path', sa.String(length=255), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('days_remaining', sa.Integer(), nullable=True),
        # The unique constraint is what makes the sweep idempotent AND
        # gives escalation for free: the key carries the severity, so
        # re-running today changes nothing but a deadline moving from
        # "10 days out" to "2 days out" raises a genuinely new alert.
        sa.Column('dedupe_key', sa.String(length=255), nullable=False),
        sa.Column(
            'is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')
        ),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dedupe_key', name='uq_notifications_dedupe_key'),
    )
    op.create_index(
        op.f('ix_notifications_project_id'), 'notifications', ['project_id']
    )
    op.create_index(op.f('ix_notifications_category'), 'notifications', ['category'])
    op.create_index(op.f('ix_notifications_severity'), 'notifications', ['severity'])
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'])
    op.create_index(
        op.f('ix_notifications_created_at'), 'notifications', ['created_at']
    )
    op.create_index(
        op.f('ix_notifications_dedupe_key'), 'notifications', ['dedupe_key']
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f('ix_notifications_dedupe_key'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_severity'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_category'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_project_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_variations_status'), table_name='variations')
    op.drop_index(op.f('ix_variations_project_id'), table_name='variations')
    op.drop_table('variations')

    op.drop_index(op.f('ix_determinations_status'), table_name='determinations')
    op.drop_index(op.f('ix_determinations_claim_id'), table_name='determinations')
    op.drop_index(op.f('ix_determinations_project_id'), table_name='determinations')
    op.drop_table('determinations')

    op.drop_index(op.f('ix_compliance_runs_run_date'), table_name='compliance_runs')
    op.drop_table('compliance_runs')

    op.drop_index(
        op.f('ix_compliance_obligations_status'), table_name='compliance_obligations'
    )
    op.drop_index(
        op.f('ix_compliance_obligations_due_date'),
        table_name='compliance_obligations',
    )
    op.drop_index(
        op.f('ix_compliance_obligations_project_id'),
        table_name='compliance_obligations',
    )
    op.drop_table('compliance_obligations')

    op.drop_column('projects', 'compliance_alert_lead_days')
    op.drop_column('projects', 'variation_proposal_period_days')
    op.drop_column('projects', 'deemed_variation_notice_days')
    op.drop_column('projects', 'nod_period_days')
    op.drop_column('projects', 'engineer_determination_period_days')
    op.drop_column('projects', 'statement_due_days')
    op.drop_column('projects', 'progress_report_due_days')
    op.drop_column('projects', 'defects_notification_period_days')
    op.drop_column('projects', 'performance_certificate_date')
    op.drop_column('projects', 'taking_over_date')
    op.drop_column('projects', 'letter_of_acceptance_date')
    op.drop_column('projects', 'contract_edition')
