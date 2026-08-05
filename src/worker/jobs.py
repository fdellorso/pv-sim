"""Simulation job definitions: engine pipeline execution and result persistence."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.engine.battery_model import BatteryParams
from src.engine.economic_model import EconomicParams, EconomicResult, run_economics
from src.engine.load_model import generate_synthetic_curve, load_curve_from_csv
from src.engine.optimizer import ScenarioResult, sweep_capacities
from src.engine.pv_model import PVSystemParams, run_pv_model
from src.engine.weather import get_weather
from src.web.config import get_settings
from src.web.models import (
    LoadProfile,
    OptimizationScenario,
    Simulation,
    SimulationMetrics,
    SimulationResult,
)

DT_HOURS = 0.25


@dataclass
class PipelineResult:
    economic: EconomicResult
    pv_year1: pd.Series
    load_year1: pd.Series


def _build_base_inputs(
    sim: Simulation,
    load_profile: LoadProfile | None,
) -> tuple[pd.Series, pd.Series, EconomicParams, BatteryParams]:
    """Build the year-1 PV/load series and the base economic/battery params."""
    weather = get_weather(sim.lat, sim.lon, sim.tz)
    pv = run_pv_model(
        weather,
        PVSystemParams(
            lat=sim.lat,
            lon=sim.lon,
            tz=sim.tz,
            power_kw=sim.pv_power_kw,
            tilt=sim.tilt,
            azimuth=sim.azimuth,
            inverter_power_kw=sim.inverter_power_kw,
            system_losses_pct=sim.system_losses_pct,
        ),
    )

    if load_profile is not None:
        load = load_curve_from_csv(load_profile.file_path, sim.tz)
    else:
        load = generate_synthetic_curve(pv.index, sim.annual_consumption_kwh or 0.0)

    battery = BatteryParams(
        capacity_kwh=sim.battery_capacity_kwh or 0.0,
        c_rate=sim.battery_c_rate or 0.5,
        efficiency=(sim.battery_efficiency_pct or 95.0) / 100,
        soc_min_pct=sim.battery_soc_min_pct or 10.0,
        soc_max_pct=sim.battery_soc_max_pct or 90.0,
        degradation_pct_year=sim.battery_degradation_pct_year or 2.0,
    )
    economic = EconomicParams(
        horizon_years=sim.horizon_years,
        investment_cost_eur=sim.investment_cost_eur,
        purchase_eur_kwh=sim.purchase_eur_kwh,
        sell_eur_kwh=sim.sell_eur_kwh,
        maintenance_annual_eur=sim.maintenance_annual_eur,
        inverter_replacement_cost_eur=sim.inverter_replacement_cost_eur,
        inverter_replace_at_year=sim.inverter_replace_at_year,
        battery_replacement_cost_eur=sim.battery_replacement_cost_eur,
        battery_replace_at_year=sim.battery_replace_at_year,
        grid_activation_eur=sim.grid_activation_eur,
        grid_annual_eur=sim.grid_annual_eur,
        loan_interest_pct=sim.loan_interest_pct,
        loan_years=sim.loan_years,
        pv_degradation_pct_year=sim.pv_degradation_pct_year,
    )
    return pv, load, economic, battery


def _run_pipeline(sim: Simulation, load_profile: LoadProfile | None) -> PipelineResult:
    """Run the engine pipeline (weather → pv → load → battery → economics).

    Pure synchronous computation; CPU-heavy work is offloaded to a thread by
    the caller. Reads only plain attributes from the ORM objects.
    """
    pv, load, economic, battery = _build_base_inputs(sim, load_profile)
    return PipelineResult(
        economic=run_economics(pv, load, economic, battery, DT_HOURS),
        pv_year1=pv,
        load_year1=load,
    )


def _to_result_rows(simulation_id: int, economic: EconomicResult) -> list[SimulationResult]:
    return [
        SimulationResult(
            simulation_id=simulation_id,
            year=entry.year,
            pv_production_kwh=entry.pv_production_kwh,
            load_consumption_kwh=entry.load_consumption_kwh,
            self_consumption_kwh=entry.self_consumption_kwh,
            self_consumption_pct=entry.self_consumption_pct,
            autosufficienza_pct=entry.autosufficienza_pct,
            grid_export_kwh=entry.grid_export_kwh,
            grid_import_kwh=entry.grid_import_kwh,
            battery_energy_in_kwh=entry.battery_charge_kwh,
            battery_energy_out_kwh=entry.battery_discharge_kwh,
            battery_capacity_available_kwh=entry.battery_capacity_kwh,
            revenue_sold_eur=entry.revenue_eur,
            savings_self_consumption_eur=entry.savings_eur,
            maintenance_cost_eur=entry.maintenance_cost_eur,
            replacement_cost_eur=entry.replacement_cost_eur,
            grid_cost_eur=entry.grid_cost_eur,
            loan_payment_eur=entry.loan_payment_eur,
            net_cashflow_eur=entry.net_cashflow_eur,
            cumulative_cashflow_eur=entry.cumulative_cashflow_eur,
        )
        for entry in economic.annual
    ]


def _to_metrics(simulation_id: int, economic: EconomicResult) -> SimulationMetrics:
    total_autoconsumo = sum(e.self_consumption_pct for e in economic.annual) / len(economic.annual)
    total_autosufficienza = sum(e.autosufficienza_pct for e in economic.annual) / len(economic.annual)
    return SimulationMetrics(
        simulation_id=simulation_id,
        npv_eur=economic.npv_eur,
        irr_pct=economic.irr_pct or 0.0,
        payback_years=economic.payback_years,
        total_autoconsumo_pct=total_autoconsumo,
        total_autosufficienza_pct=total_autosufficienza,
        battery_cycles_total=None,
    )


async def run_simulation(ctx: dict, simulation_id: int) -> dict[str, object]:
    """Execute the simulation pipeline and persist results for ``simulation_id``.

    Drives the job lifecycle in the ``simulations`` table:
    ``queued`` → ``running`` → ``completed`` | ``failed``.
    """
    session_factory: async_sessionmaker[AsyncSession] = ctx["db_session"]
    async with session_factory() as session:
        sim = await session.get(Simulation, simulation_id)
        if sim is None:
            raise ValueError(f"Simulation {simulation_id} not found")

        load_profile = None
        if sim.load_profile_id is not None:
            load_profile = await session.get(LoadProfile, sim.load_profile_id)

        sim.status = "running"
        sim.error_message = None
        await session.commit()

        try:
            pipeline = await asyncio.to_thread(_run_pipeline, sim, load_profile)
        except Exception as exc:  # noqa: BLE001 — any failure marks the job failed
            sim.status = "failed"
            sim.error_message = str(exc)
            await session.commit()
            raise

        _write_curves(simulation_id, pipeline.pv_year1, pipeline.load_year1)
        session.add_all(_to_result_rows(simulation_id, pipeline.economic))
        session.add(_to_metrics(simulation_id, pipeline.economic))
        sim.status = "completed"
        await session.commit()

    return {"simulation_id": simulation_id, "status": "completed"}


def _write_curves(simulation_id: int, pv: pd.Series, load: pd.Series) -> None:
    """Persist the year-1 15-minute series as JSON for the dashboard charts."""
    data_dir = Path(get_settings().simulation_data_dir) / str(simulation_id)
    data_dir.mkdir(parents=True, exist_ok=True)

    def serialize(series: pd.Series) -> dict:
        index = cast(pd.DatetimeIndex, series.index)
        start = cast(pd.Timestamp, index[0])
        if index.tz is not None:
            start = start.tz_localize(None)
        return {
            "start": str(start),
            "freq": "15min",
            "tz": str(index.tz) if index.tz is not None else None,
            "values": [float(v) for v in series.to_numpy()],
        }

    (data_dir / "pv_year1.json").write_text(json.dumps(serialize(pv)))
    (data_dir / "load_year1.json").write_text(json.dumps(serialize(load)))


async def run_optimization(ctx: dict, payload: dict) -> dict[str, object]:
    """Sweep battery capacities for a set of simulation parameters.

    Creates one ``Simulation`` row per capacity plus the
    ``OptimizationScenario`` rows used by the comparison page. ``payload``
    holds the validated simulation parameters and the optimizer config
    (``capacities``, battery costs, ``optimization_group`` UUID).
    """
    sim_params: dict = payload["simulation"]
    group = str(payload["optimization_group"])
    capacities: list[float] = [float(c) for c in payload["capacities"]]
    cost_per_kwh = float(payload["battery_cost_eur_per_kwh"])
    replace_per_kwh = float(payload["battery_replace_eur_per_kwh"])

    session_factory: async_sessionmaker[AsyncSession] = ctx["db_session"]
    async with session_factory() as session:
        simulations: list[tuple[Simulation, float]] = []
        for capacity in capacities:
            sim = Simulation(**sim_params)
            sim.name = f"{sim_params.get('name', 'Ottimizzazione')} — {capacity:g} kWh"
            session.add(sim)
            await session.flush()
            session.add(
                OptimizationScenario(
                    optimization_group=group,
                    simulation_id=sim.id,
                    capacity_kwh=capacity,
                )
            )
            simulations.append((sim, capacity))
        await session.commit()

        template = Simulation(**sim_params)
        load_profile = None
        if template.load_profile_id is not None:
            load_profile = await session.get(LoadProfile, template.load_profile_id)

        try:
            pv, load, economic, battery = await asyncio.to_thread(
                _build_base_inputs, template, load_profile
            )
            results: list[ScenarioResult] = await asyncio.to_thread(
                sweep_capacities,
                pv,
                load,
                economic,
                battery,
                capacities,
                cost_per_kwh,
                replace_per_kwh,
            )
        except Exception as exc:  # noqa: BLE001
            for sim, _capacity in simulations:
                sim.status = "failed"
                sim.error_message = str(exc)
            await session.commit()
            raise

        results_by_capacity = {r.capacity_kwh: r for r in results}
        best_capacity = results[0].capacity_kwh if results else None

        for sim, capacity in simulations:
            scenario = (
                await session.execute(
                    select(OptimizationScenario).where(
                        OptimizationScenario.simulation_id == sim.id
                    )
                )
            ).scalar_one()
            result = results_by_capacity.get(capacity)
            if result is None:
                sim.status = "failed"
                sim.error_message = "Scenario non calcolato"
                await session.commit()
                continue

            sim.status = "completed"
            sim.battery_capacity_kwh = capacity
            session.add_all(_to_result_rows(sim.id, result.economic))
            session.add(_to_metrics(sim.id, result.economic))
            scenario.npv_eur = result.npv_eur
            scenario.irr_pct = result.irr_pct
            scenario.payback_years = result.payback_years
            scenario.autoconsumo_pct = result.autoconsumo_pct
            scenario.autosufficienza_pct = result.autosufficienza_pct
            await session.commit()
            if best_capacity is not None and capacity == best_capacity:
                _write_curves(sim.id, pv, load)

    return {"optimization_group": group, "scenarios": len(capacities)}
