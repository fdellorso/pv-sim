"""Optimization routes: sweep battery capacities and compare scenarios."""

from __future__ import annotations

import re
import uuid
from typing import Literal

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.web.database import get_session
from src.web.models import OptimizationScenario, Simulation
from src.web.routes.simulations import SimulationCreate
from src.web.templating import templates

api_router = APIRouter(prefix="/api/optimizations", tags=["optimizations"])
page_router = APIRouter(tags=["pages"])

_STATUS_RANK = {"completed": 0, "running": 1, "queued": 2, "failed": 3}
_CAPACITY_SUFFIX = re.compile(r" — [\d.]+ kWh$")


class OptimizationCreate(SimulationCreate):
    mode: Literal["sweep", "manual"] = "sweep"
    min_capacity: float = Field(ge=0, default=0.0)
    max_capacity: float = Field(gt=0, default=20.0)
    step: float = Field(gt=0, default=2.5)
    capacities: str = ""
    battery_cost_eur_per_kwh: float = Field(ge=0, default=600.0)
    battery_replace_eur_per_kwh: float = Field(ge=0, default=400.0)


def _build_capacities(payload: OptimizationCreate) -> list[float]:
    if payload.mode == "manual":
        values = [float(v.strip()) for v in payload.capacities.split(",") if v.strip()]
        if not values:
            raise HTTPException(status_code=422, detail="Inserire almeno una capacità")
        return sorted(values)
    values = np.arange(payload.min_capacity, payload.max_capacity + payload.step / 2, payload.step)
    return [round(float(v), 3) for v in values]


def _scenario_to_dict(scenario: OptimizationScenario, sim: Simulation) -> dict:
    return {
        "simulation_id": sim.id,
        "capacity_kwh": scenario.capacity_kwh,
        "status": sim.status,
        "error_message": sim.error_message,
        "npv_eur": scenario.npv_eur,
        "irr_pct": scenario.irr_pct,
        "payback_years": scenario.payback_years,
        "autoconsumo_pct": scenario.autoconsumo_pct,
        "autosufficienza_pct": scenario.autosufficienza_pct,
    }


async def _load_group(session: AsyncSession, group: str) -> dict:
    rows = (
        await session.execute(
            select(OptimizationScenario, Simulation)
            .join(Simulation, OptimizationScenario.simulation_id == Simulation.id)
            .where(OptimizationScenario.optimization_group == group)
        )
    ).all()
    if not rows:
        raise HTTPException(status_code=404, detail="ottimizzazione non trovata")

    scenarios = [_scenario_to_dict(scenario, sim) for scenario, sim in rows]
    scenarios.sort(
        key=lambda s: (
            _STATUS_RANK[s["status"]],
            -(s["npv_eur"] if s["npv_eur"] is not None else float("-inf")),
        )
    )
    completed = [s for s in scenarios if s["status"] == "completed"]
    best = completed[0] if completed else None

    first_name = rows[0][1].name
    title = _CAPACITY_SUFFIX.sub("", first_name)
    return {
        "optimization_group": group,
        "title": title,
        "total": len(scenarios),
        "completed": sum(1 for s in scenarios if s["status"] == "completed"),
        "failed": sum(1 for s in scenarios if s["status"] == "failed"),
        "done": all(s["status"] in ("completed", "failed") for s in scenarios),
        "best": best,
        "scenarios": scenarios,
    }


@api_router.post("", status_code=202)
async def create_optimization(
    payload: OptimizationCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create the optimization group and enqueue the sweep job."""
    if payload.load_profile_id is None and payload.annual_consumption_kwh is None:
        raise HTTPException(
            status_code=422, detail="load_profile_id or annual_consumption_kwh is required"
        )

    capacities = _build_capacities(payload)
    if len(capacities) > 30:
        raise HTTPException(status_code=422, detail="Troppi scenari (max 30)")

    group = uuid.uuid4().hex
    sim_params = payload.model_dump(
        exclude={
            "mode",
            "min_capacity",
            "max_capacity",
            "step",
            "capacities",
            "battery_cost_eur_per_kwh",
            "battery_replace_eur_per_kwh",
        }
    )
    sim_params["battery_capacity_kwh"] = None

    await request.app.state.arq.enqueue_job(
        "run_optimization",
        {
            "simulation": sim_params,
            "optimization_group": group,
            "capacities": capacities,
            "battery_cost_eur_per_kwh": payload.battery_cost_eur_per_kwh,
            "battery_replace_eur_per_kwh": payload.battery_replace_eur_per_kwh,
        },
    )
    return {"optimization_group": group, "scenarios": len(capacities)}


@api_router.get("/{group}")
async def get_optimization(
    group: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await _load_group(session, group)


@page_router.get("/optimizations/{group}")
async def optimization_page(
    group: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    await _load_group(session, group)
    return templates.TemplateResponse(
        request,
        "optimization_group.html",
        {"optimization_group": group},
    )


@page_router.get("/optimizations/{group}/status")
async def optimization_status_fragment(
    group: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    data = await _load_group(session, group)
    return templates.TemplateResponse(
        request,
        "optimization_fragment.html",
        {"data": data},
    )
