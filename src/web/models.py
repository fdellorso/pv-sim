"""SQLAlchemy ORM models (schema managed by Alembic)."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    tz: Mapped[str] = mapped_column(Text)

    pv_power_kw: Mapped[float] = mapped_column(Float)
    tilt: Mapped[float] = mapped_column(Float)
    azimuth: Mapped[float] = mapped_column(Float)
    inverter_power_kw: Mapped[float] = mapped_column(Float)
    system_losses_pct: Mapped[float] = mapped_column(Float, default=14.0)
    pv_degradation_pct_year: Mapped[float] = mapped_column(Float, default=0.5)

    battery_capacity_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_c_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_efficiency_pct: Mapped[float | None] = mapped_column(Float, nullable=True, default=95.0)
    battery_degradation_pct_year: Mapped[float | None] = mapped_column(Float, nullable=True, default=2.0)
    battery_soc_min_pct: Mapped[float | None] = mapped_column(Float, nullable=True, default=10.0)
    battery_soc_max_pct: Mapped[float | None] = mapped_column(Float, nullable=True, default=90.0)
    battery_replace_at_year: Mapped[int | None] = mapped_column(Integer, nullable=True, default=12)

    load_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("load_profiles.id", ondelete="SET NULL"), nullable=True
    )
    annual_consumption_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    purchase_eur_kwh: Mapped[float] = mapped_column(Float)
    sell_eur_kwh: Mapped[float] = mapped_column(Float)

    horizon_years: Mapped[int] = mapped_column(Integer)
    investment_cost_eur: Mapped[float] = mapped_column(Float)
    loan_interest_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    loan_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maintenance_annual_eur: Mapped[float] = mapped_column(Float, default=0.0)
    inverter_replace_at_year: Mapped[int | None] = mapped_column(Integer, nullable=True, default=10)
    inverter_replacement_cost_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_replacement_cost_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_activation_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_annual_eur: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LoadProfile(Base):
    __tablename__ = "load_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    profile_type: Mapped[str] = mapped_column(Text, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    annual_consumption_kwh: Mapped[float] = mapped_column(Float)
    file_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SimulationResult(Base):
    __tablename__ = "simulation_results"
    __table_args__ = (
        UniqueConstraint("simulation_id", "year", name="uq_simulation_results_sim_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(
        ForeignKey("simulations.id", ondelete="CASCADE"), index=True
    )
    year: Mapped[int] = mapped_column(Integer)

    pv_production_kwh: Mapped[float] = mapped_column(Float)
    load_consumption_kwh: Mapped[float] = mapped_column(Float)
    self_consumption_kwh: Mapped[float] = mapped_column(Float)
    self_consumption_pct: Mapped[float] = mapped_column(Float)
    autosufficienza_pct: Mapped[float] = mapped_column(Float)
    grid_export_kwh: Mapped[float] = mapped_column(Float)
    grid_import_kwh: Mapped[float] = mapped_column(Float)

    battery_energy_in_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_energy_out_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_capacity_available_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    revenue_sold_eur: Mapped[float] = mapped_column(Float)
    savings_self_consumption_eur: Mapped[float] = mapped_column(Float)
    maintenance_cost_eur: Mapped[float] = mapped_column(Float)
    replacement_cost_eur: Mapped[float] = mapped_column(Float)
    grid_cost_eur: Mapped[float] = mapped_column(Float)
    loan_payment_eur: Mapped[float] = mapped_column(Float)
    net_cashflow_eur: Mapped[float] = mapped_column(Float)
    cumulative_cashflow_eur: Mapped[float] = mapped_column(Float)


class SimulationMetrics(Base):
    __tablename__ = "simulation_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(
        ForeignKey("simulations.id", ondelete="CASCADE"), unique=True
    )
    npv_eur: Mapped[float] = mapped_column(Float)
    irr_pct: Mapped[float] = mapped_column(Float)
    payback_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_autoconsumo_pct: Mapped[float] = mapped_column(Float)
    total_autosufficienza_pct: Mapped[float] = mapped_column(Float)
    battery_cycles_total: Mapped[float | None] = mapped_column(Float, nullable=True)


class OptimizationScenario(Base):
    __tablename__ = "optimization_scenarios"
    __table_args__ = (
        UniqueConstraint("optimization_group", "simulation_id", name="uq_optimization_group_sim"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    optimization_group: Mapped[str] = mapped_column(Text, index=True)
    simulation_id: Mapped[int] = mapped_column(
        ForeignKey("simulations.id", ondelete="CASCADE"), index=True
    )
    capacity_kwh: Mapped[float] = mapped_column(Float)
    npv_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    irr_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    payback_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    autoconsumo_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    autosufficienza_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
