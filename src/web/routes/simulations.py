"""Simulation routes: create + enqueue, JSON status, HTMX status polling."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.web.charts import cashflow_figure, daily_curves_figure, read_curves
from src.web.config import get_settings
from src.web.database import get_session
from src.web.models import LoadProfile, Simulation, SimulationMetrics, SimulationResult
from src.web.report import build_report_pdf
from src.web.templating import templates

api_router = APIRouter(prefix="/api/simulations", tags=["simulations"])
page_router = APIRouter(tags=["pages"])


class SimulationCreate(BaseModel):
    name: str = Field(min_length=1)
    lat: float
    lon: float
    tz: str
    pv_power_kw: float = Field(gt=0)
    tilt: float = 0.0
    azimuth: float = 0.0
    inverter_power_kw: float = Field(gt=0)
    system_losses_pct: float = 14.0
    pv_degradation_pct_year: float = 0.5

    battery_capacity_kwh: float | None = None
    battery_c_rate: float | None = None
    battery_efficiency_pct: float | None = 95.0
    battery_degradation_pct_year: float | None = 2.0
    battery_soc_min_pct: float | None = 10.0
    battery_soc_max_pct: float | None = 90.0
    battery_replace_at_year: int | None = 12

    load_profile_id: int | None = None
    annual_consumption_kwh: float | None = None

    purchase_eur_kwh: float = Field(ge=0)
    sell_eur_kwh: float = Field(ge=0)

    horizon_years: int = Field(ge=1)
    investment_cost_eur: float = Field(ge=0)
    loan_interest_pct: float | None = None
    loan_years: int | None = None
    maintenance_annual_eur: float = 0.0
    inverter_replace_at_year: int | None = 10
    inverter_replacement_cost_eur: float | None = None
    battery_replacement_cost_eur: float | None = None
    grid_activation_eur: float | None = None
    grid_annual_eur: float | None = None


def _result_to_dict(row: SimulationResult) -> dict:
    return {
        "year": row.year,
        "pv_production_kwh": row.pv_production_kwh,
        "load_consumption_kwh": row.load_consumption_kwh,
        "self_consumption_kwh": row.self_consumption_kwh,
        "self_consumption_pct": row.self_consumption_pct,
        "autosufficienza_pct": row.autosufficienza_pct,
        "grid_export_kwh": row.grid_export_kwh,
        "grid_import_kwh": row.grid_import_kwh,
        "battery_energy_in_kwh": row.battery_energy_in_kwh,
        "battery_energy_out_kwh": row.battery_energy_out_kwh,
        "battery_capacity_available_kwh": row.battery_capacity_available_kwh,
        "revenue_sold_eur": row.revenue_sold_eur,
        "savings_self_consumption_eur": row.savings_self_consumption_eur,
        "maintenance_cost_eur": row.maintenance_cost_eur,
        "replacement_cost_eur": row.replacement_cost_eur,
        "grid_cost_eur": row.grid_cost_eur,
        "loan_payment_eur": row.loan_payment_eur,
        "net_cashflow_eur": row.net_cashflow_eur,
        "cumulative_cashflow_eur": row.cumulative_cashflow_eur,
    }


def _metrics_to_dict(metrics: SimulationMetrics) -> dict:
    return {
        "npv_eur": metrics.npv_eur,
        "irr_pct": metrics.irr_pct,
        "payback_years": metrics.payback_years,
        "total_autoconsumo_pct": metrics.total_autoconsumo_pct,
        "total_autosufficienza_pct": metrics.total_autosufficienza_pct,
        "battery_cycles_total": metrics.battery_cycles_total,
    }


async def _load_results(
    session: AsyncSession, simulation_id: int
) -> tuple[SimulationMetrics | None, list[SimulationResult]]:
    metrics = (
        await session.execute(
            select(SimulationMetrics).where(SimulationMetrics.simulation_id == simulation_id)
        )
    ).scalar_one_or_none()
    rows = (
        (
            await session.execute(
                select(SimulationResult)
                .where(SimulationResult.simulation_id == simulation_id)
                .order_by(SimulationResult.year)
            )
        )
        .scalars()
        .all()
    )
    return metrics, list(rows)


@api_router.get("/{simulation_id}/report.pdf")
async def download_report(
    simulation_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Return the simulation report as a PDF attachment."""
    sim = await session.get(Simulation, simulation_id)
    if sim is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    if sim.status != "completed":
        raise HTTPException(status_code=409, detail="simulation not completed")

    metrics, rows = await _load_results(session, simulation_id)
    if metrics is None:
        raise HTTPException(status_code=409, detail="simulation not completed")

    curves = read_curves(simulation_id)
    pdf = await asyncio.to_thread(build_report_pdf, sim, metrics, rows, curves)
    filename = f"report_{simulation_id}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_router.delete("/{simulation_id}", status_code=204)
async def delete_simulation(
    simulation_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a simulation, its results/metrics (DB cascade) and curve files."""
    sim = await session.get(Simulation, simulation_id)
    if sim is None:
        raise HTTPException(status_code=404, detail="simulation not found")

    await session.delete(sim)
    await session.commit()

    curves_dir = Path(get_settings().simulation_data_dir) / str(simulation_id)
    shutil.rmtree(curves_dir, ignore_errors=True)
    return Response(status_code=204)


@api_router.post("", status_code=202)
async def create_simulation(
    payload: SimulationCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Persist a simulation row and enqueue the worker job."""
    if payload.load_profile_id is None and payload.annual_consumption_kwh is None:
        raise HTTPException(
            status_code=422, detail="load_profile_id or annual_consumption_kwh is required"
        )
    if payload.load_profile_id is not None:
        profile = await session.get(LoadProfile, payload.load_profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="load profile not found")

    sim = Simulation(**payload.model_dump())
    session.add(sim)
    await session.commit()
    await session.refresh(sim)

    await request.app.state.arq.enqueue_job("run_simulation", sim.id)
    return {"id": sim.id, "status": sim.status}


@api_router.get("/{simulation_id}")
async def get_simulation(
    simulation_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return simulation status plus results/metrics once completed."""
    sim = await session.get(Simulation, simulation_id)
    if sim is None:
        raise HTTPException(status_code=404, detail="simulation not found")

    metrics, rows = await _load_results(session, simulation_id)
    return {
        "id": sim.id,
        "name": sim.name,
        "status": sim.status,
        "error_message": sim.error_message,
        "metrics": _metrics_to_dict(metrics) if metrics else None,
        "results": [_result_to_dict(row) for row in rows] or None,
    }


@page_router.get("/simulations/{simulation_id}")
async def simulation_status_page(
    simulation_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Dashboard page: polls the status fragment until the job completes."""
    sim = await session.get(Simulation, simulation_id)
    if sim is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    return templates.TemplateResponse(
        request,
        "simulation_status.html",
        {"simulation": sim},
    )


@page_router.get("/simulations/{simulation_id}/status")
async def simulation_status_fragment(
    simulation_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """HTMX-pollable fragment: spinner while running, dashboard once complete."""
    sim = await session.get(Simulation, simulation_id)
    if sim is None:
        raise HTTPException(status_code=404, detail="simulation not found")

    metrics, rows = await _load_results(session, simulation_id)

    figures: dict[str, str] = {}
    if sim.status == "completed" and metrics is not None:
        curves = read_curves(simulation_id)
        if curves is not None:
            pv, load = curves
            figures["daily"] = cast(str, daily_curves_figure(pv, load).to_json())
        if rows:
            figures["cashflow"] = cast(str, cashflow_figure(rows).to_json())

    return templates.TemplateResponse(
        request,
        "status_fragment.html",
        {
            "simulation": sim,
            "metrics": metrics,
            "results": rows,
            "figures": figures,
        },
    )
