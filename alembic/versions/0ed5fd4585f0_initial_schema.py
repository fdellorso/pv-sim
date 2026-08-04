"""initial schema

Revision ID: 0ed5fd4585f0
Revises: 
Create Date: 2026-08-04 23:21:36.001273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ed5fd4585f0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('load_profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('source_type', sa.Text(), nullable=False),
    sa.Column('profile_type', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('annual_consumption_kwh', sa.Float(), nullable=False),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_load_profiles'))
    )
    op.create_index(op.f('ix_load_profiles_profile_type'), 'load_profiles', ['profile_type'], unique=False)
    op.create_table('simulations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=False),
    sa.Column('lon', sa.Float(), nullable=False),
    sa.Column('tz', sa.Text(), nullable=False),
    sa.Column('pv_power_kw', sa.Float(), nullable=False),
    sa.Column('tilt', sa.Float(), nullable=False),
    sa.Column('azimuth', sa.Float(), nullable=False),
    sa.Column('inverter_power_kw', sa.Float(), nullable=False),
    sa.Column('system_losses_pct', sa.Float(), nullable=False),
    sa.Column('pv_degradation_pct_year', sa.Float(), nullable=False),
    sa.Column('battery_capacity_kwh', sa.Float(), nullable=True),
    sa.Column('battery_c_rate', sa.Float(), nullable=True),
    sa.Column('battery_efficiency_pct', sa.Float(), nullable=True),
    sa.Column('battery_degradation_pct_year', sa.Float(), nullable=True),
    sa.Column('battery_soc_min_pct', sa.Float(), nullable=True),
    sa.Column('battery_soc_max_pct', sa.Float(), nullable=True),
    sa.Column('battery_replace_at_year', sa.Integer(), nullable=True),
    sa.Column('load_profile_id', sa.Integer(), nullable=True),
    sa.Column('annual_consumption_kwh', sa.Float(), nullable=True),
    sa.Column('purchase_eur_kwh', sa.Float(), nullable=False),
    sa.Column('sell_eur_kwh', sa.Float(), nullable=False),
    sa.Column('horizon_years', sa.Integer(), nullable=False),
    sa.Column('investment_cost_eur', sa.Float(), nullable=False),
    sa.Column('loan_interest_pct', sa.Float(), nullable=True),
    sa.Column('loan_years', sa.Integer(), nullable=True),
    sa.Column('maintenance_annual_eur', sa.Float(), nullable=False),
    sa.Column('inverter_replace_at_year', sa.Integer(), nullable=True),
    sa.Column('inverter_replacement_cost_eur', sa.Float(), nullable=True),
    sa.Column('battery_replacement_cost_eur', sa.Float(), nullable=True),
    sa.Column('grid_activation_eur', sa.Float(), nullable=True),
    sa.Column('grid_annual_eur', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['load_profile_id'], ['load_profiles.id'], name=op.f('fk_simulations_load_profile_id_load_profiles'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_simulations'))
    )
    op.create_index(op.f('ix_simulations_status'), 'simulations', ['status'], unique=False)
    op.create_table('simulation_metrics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('simulation_id', sa.Integer(), nullable=False),
    sa.Column('npv_eur', sa.Float(), nullable=False),
    sa.Column('irr_pct', sa.Float(), nullable=False),
    sa.Column('payback_years', sa.Float(), nullable=True),
    sa.Column('total_autoconsumo_pct', sa.Float(), nullable=False),
    sa.Column('total_autosufficienza_pct', sa.Float(), nullable=False),
    sa.Column('battery_cycles_total', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], name=op.f('fk_simulation_metrics_simulation_id_simulations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_simulation_metrics')),
    sa.UniqueConstraint('simulation_id', name=op.f('uq_simulation_metrics_simulation_id'))
    )
    op.create_table('simulation_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('simulation_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('pv_production_kwh', sa.Float(), nullable=False),
    sa.Column('load_consumption_kwh', sa.Float(), nullable=False),
    sa.Column('self_consumption_kwh', sa.Float(), nullable=False),
    sa.Column('self_consumption_pct', sa.Float(), nullable=False),
    sa.Column('autosufficienza_pct', sa.Float(), nullable=False),
    sa.Column('grid_export_kwh', sa.Float(), nullable=False),
    sa.Column('grid_import_kwh', sa.Float(), nullable=False),
    sa.Column('battery_energy_in_kwh', sa.Float(), nullable=True),
    sa.Column('battery_energy_out_kwh', sa.Float(), nullable=True),
    sa.Column('battery_capacity_available_kwh', sa.Float(), nullable=True),
    sa.Column('revenue_sold_eur', sa.Float(), nullable=False),
    sa.Column('savings_self_consumption_eur', sa.Float(), nullable=False),
    sa.Column('maintenance_cost_eur', sa.Float(), nullable=False),
    sa.Column('replacement_cost_eur', sa.Float(), nullable=False),
    sa.Column('grid_cost_eur', sa.Float(), nullable=False),
    sa.Column('loan_payment_eur', sa.Float(), nullable=False),
    sa.Column('net_cashflow_eur', sa.Float(), nullable=False),
    sa.Column('cumulative_cashflow_eur', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], name=op.f('fk_simulation_results_simulation_id_simulations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_simulation_results')),
    sa.UniqueConstraint('simulation_id', 'year', name='uq_simulation_results_sim_year')
    )
    op.create_index(op.f('ix_simulation_results_simulation_id'), 'simulation_results', ['simulation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_simulation_results_simulation_id'), table_name='simulation_results')
    op.drop_table('simulation_results')
    op.drop_table('simulation_metrics')
    op.drop_index(op.f('ix_simulations_status'), table_name='simulations')
    op.drop_table('simulations')
    op.drop_index(op.f('ix_load_profiles_profile_type'), table_name='load_profiles')
    op.drop_table('load_profiles')
