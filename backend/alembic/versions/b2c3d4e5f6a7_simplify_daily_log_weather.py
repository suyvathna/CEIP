"""simplify daily log weather + add rain records

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('daily_logs', 'temp_low_c')
    op.drop_column('daily_logs', 'temp_high_c')
    op.drop_column('daily_logs', 'precip_since_midnight_mm')
    op.drop_column('daily_logs', 'precip_2_days_ago_mm')
    op.drop_column('daily_logs', 'precip_3_days_ago_mm')
    op.drop_column('daily_logs', 'humidity_low_pct')
    op.drop_column('daily_logs', 'humidity_high_pct')
    op.drop_column('daily_logs', 'dew_point_c')
    op.drop_column('daily_logs', 'wind_avg_kmh')
    op.drop_column('daily_logs', 'wind_max_kmh')
    op.drop_column('daily_logs', 'wind_gust_kmh')

    op.drop_column('daily_log_weather_observations', 'sky')
    op.drop_column('daily_log_weather_observations', 'temp_avg_c')
    op.drop_column('daily_log_weather_observations', 'precipitation')
    op.drop_column('daily_log_weather_observations', 'wind')
    op.drop_column('daily_log_weather_observations', 'ground_condition')
    op.drop_column('daily_log_weather_observations', 'calamity')
    op.alter_column(
        'daily_log_weather_observations', 'observed_time', new_column_name='start_time'
    )
    op.add_column(
        'daily_log_weather_observations', sa.Column('end_time', sa.Time(), nullable=True)
    )
    op.add_column(
        'daily_log_weather_observations',
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_weather_observations_evidence_id',
        'daily_log_weather_observations',
        'evidence',
        ['evidence_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_weather_observations_evidence_id',
        'daily_log_weather_observations',
        type_='foreignkey',
    )
    op.drop_column('daily_log_weather_observations', 'evidence_id')
    op.drop_column('daily_log_weather_observations', 'end_time')
    op.alter_column(
        'daily_log_weather_observations', 'start_time', new_column_name='observed_time'
    )
    op.add_column('daily_log_weather_observations', sa.Column('calamity', sa.String(100), nullable=True))
    op.add_column('daily_log_weather_observations', sa.Column('ground_condition', sa.String(100), nullable=True))
    op.add_column('daily_log_weather_observations', sa.Column('wind', sa.String(100), nullable=True))
    op.add_column('daily_log_weather_observations', sa.Column('precipitation', sa.String(100), nullable=True))
    op.add_column('daily_log_weather_observations', sa.Column('temp_avg_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_log_weather_observations', sa.Column('sky', sa.String(100), nullable=True))

    op.add_column('daily_logs', sa.Column('wind_gust_kmh', sa.Numeric(5, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('wind_max_kmh', sa.Numeric(5, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('wind_avg_kmh', sa.Numeric(5, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('dew_point_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('humidity_high_pct', sa.Integer(), nullable=True))
    op.add_column('daily_logs', sa.Column('humidity_low_pct', sa.Integer(), nullable=True))
    op.add_column('daily_logs', sa.Column('precip_3_days_ago_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('daily_logs', sa.Column('precip_2_days_ago_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('daily_logs', sa.Column('precip_since_midnight_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('daily_logs', sa.Column('temp_high_c', sa.Numeric(4, 1), nullable=True))
    op.add_column('daily_logs', sa.Column('temp_low_c', sa.Numeric(4, 1), nullable=True))
