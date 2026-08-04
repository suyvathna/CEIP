"""Daily Diary -> Daily Log: rename tables/columns to match the new name,
and add the structured sections from the reference site-log template -
Weather Report, Daily Snapshot, Observed Weather Conditions, Manpower
Log, Equipment Log, Delivery Log, Inspection Log, HSE, Visitors - plus
letting Photos (Evidence) attach directly to a Daily Log instead of only
to an Event.

Revision ID: d1e2f3a4b5c6
Revises: c3d9a1f5e6b2
Create Date: 2026-08-01 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c3d9a1f5e6b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Rename the diary tables/columns to "daily log" ---------------
    op.rename_table('daily_diaries', 'daily_logs')
    op.rename_table('diary_event_links', 'daily_log_event_links')
    op.alter_column('daily_log_event_links', 'diary_id', new_column_name='daily_log_id')

    # The old flat free-text columns become "_notes" overflow fields -
    # the structured child tables added below now carry the per-row detail.
    op.alter_column('daily_logs', 'manpower', new_column_name='manpower_notes')
    op.alter_column('daily_logs', 'equipment', new_column_name='equipment_notes')
    op.alter_column('daily_logs', 'materials', new_column_name='materials_notes')
    op.alter_column('daily_logs', 'safety', new_column_name='hse_notes')
    op.alter_column('daily_logs', 'visitors', new_column_name='visitor_notes')

    # --- Weather Report (flat, one row per day) + Daily Snapshot -------
    op.add_column('daily_logs', sa.Column('temp_low_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('temp_high_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('temp_avg_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('precip_since_midnight_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('daily_logs', sa.Column('precip_2_days_ago_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('daily_logs', sa.Column('precip_3_days_ago_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('daily_logs', sa.Column('humidity_low_pct', sa.Integer(), nullable=True))
    op.add_column('daily_logs', sa.Column('humidity_avg_pct', sa.Integer(), nullable=True))
    op.add_column('daily_logs', sa.Column('humidity_high_pct', sa.Integer(), nullable=True))
    op.add_column('daily_logs', sa.Column('dew_point_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('wind_avg_kmh', sa.Numeric(5, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('wind_max_kmh', sa.Numeric(5, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('wind_gust_kmh', sa.Numeric(5, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('daily_snapshot', postgresql.JSONB(), nullable=True))

    # --- Observed Weather Conditions ------------------------------------
    op.create_table(
        'daily_log_weather_observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('observed_time', sa.Time(), nullable=True),
        sa.Column('caused_delay', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sky', sa.String(length=100), nullable=True),
        sa.Column('temp_avg_c', sa.Numeric(4, 1), nullable=True),
        sa.Column('precipitation', sa.String(length=100), nullable=True),
        sa.Column('wind', sa.String(length=100), nullable=True),
        sa.Column('ground_condition', sa.String(length=100), nullable=True),
        sa.Column('calamity', sa.String(length=100), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Manpower Log -----------------------------------------------------
    op.create_table(
        'daily_log_manpower_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company', sa.String(length=200), nullable=True),
        sa.Column('trade', sa.String(length=100), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('workers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('hours', sa.Numeric(5, 2), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Equipment Log ------------------------------------------------------
    op.create_table(
        'daily_log_equipment_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('equipment_name', sa.String(length=200), nullable=False),
        sa.Column('equipment_type', sa.String(length=100), nullable=True),
        sa.Column('hours_operating', sa.Numeric(4, 1), nullable=True),
        sa.Column('hours_idle', sa.Numeric(4, 1), nullable=True),
        sa.Column('inspected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('inspection_time', sa.Time(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Delivery Log -------------------------------------------------------
    op.create_table(
        'daily_log_delivery_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('delivery_time', sa.Time(), nullable=True),
        sa.Column('delivered_from', sa.String(length=200), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('contents', sa.Text(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Inspection Log -------------------------------------------------------
    op.create_table(
        'daily_log_inspection_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('inspection_type', sa.String(length=150), nullable=True),
        sa.Column('inspecting_entity', sa.String(length=150), nullable=True),
        sa.Column('inspector_name', sa.String(length=150), nullable=True),
        sa.Column('location_area', sa.String(length=150), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- HSE Log ------------------------------------------------------------
    op.create_table(
        'daily_log_hse_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_time', sa.Time(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('reported_by', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Visitor Log --------------------------------------------------------
    op.create_table(
        'daily_log_visitor_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('time_in', sa.Time(), nullable=True),
        sa.Column('time_out', sa.Time(), nullable=True),
        sa.Column('visitor_name', sa.String(length=150), nullable=True),
        sa.Column('company', sa.String(length=200), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('host_name', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Photos: let Evidence attach directly to a Daily Log -----------
    # Most Daily Log photos (deliveries, HSE findings, general progress)
    # have no corresponding Event, so event_id can no longer be required.
    op.alter_column('evidence', 'event_id', existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.add_column('evidence', sa.Column('daily_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.id'), nullable=True))
    op.add_column('evidence', sa.Column('category', sa.String(length=50), nullable=True))
    op.add_column('evidence', sa.Column('caption', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('evidence', 'caption')
    op.drop_column('evidence', 'category')
    op.drop_column('evidence', 'daily_log_id')
    # Any evidence rows created with a null event_id (i.e. Daily Log
    # photos with no Event) can't survive a downgrade to a NOT NULL
    # event_id and are left as-is here - same "best effort, not
    # data-preserving" downgrade posture as the rest of this migration
    # chain (see the manpower type-change downgrade above it).
    op.alter_column('evidence', 'event_id', existing_type=postgresql.UUID(as_uuid=True), nullable=False)

    op.drop_table('daily_log_visitor_entries')
    op.drop_table('daily_log_hse_entries')
    op.drop_table('daily_log_inspection_entries')
    op.drop_table('daily_log_delivery_entries')
    op.drop_table('daily_log_equipment_entries')
    op.drop_table('daily_log_manpower_entries')
    op.drop_table('daily_log_weather_observations')

    op.drop_column('daily_logs', 'daily_snapshot')
    op.drop_column('daily_logs', 'wind_gust_kmh')
    op.drop_column('daily_logs', 'wind_max_kmh')
    op.drop_column('daily_logs', 'wind_avg_kmh')
    op.drop_column('daily_logs', 'dew_point_c')
    op.drop_column('daily_logs', 'humidity_high_pct')
    op.drop_column('daily_logs', 'humidity_avg_pct')
    op.drop_column('daily_logs', 'humidity_low_pct')
    op.drop_column('daily_logs', 'precip_3_days_ago_mm')
    op.drop_column('daily_logs', 'precip_2_days_ago_mm')
    op.drop_column('daily_logs', 'precip_since_midnight_mm')
    op.drop_column('daily_logs', 'temp_avg_c')
    op.drop_column('daily_logs', 'temp_high_c')
    op.drop_column('daily_logs', 'temp_low_c')

    op.alter_column('daily_logs', 'visitor_notes', new_column_name='visitors')
    op.alter_column('daily_logs', 'hse_notes', new_column_name='safety')
    op.alter_column('daily_logs', 'materials_notes', new_column_name='materials')
    op.alter_column('daily_logs', 'equipment_notes', new_column_name='equipment')
    op.alter_column('daily_logs', 'manpower_notes', new_column_name='manpower')

    op.alter_column('daily_log_event_links', 'daily_log_id', new_column_name='diary_id')
    op.rename_table('daily_log_event_links', 'diary_event_links')
    op.rename_table('daily_logs', 'daily_diaries')
