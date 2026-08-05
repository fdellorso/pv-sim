"""Tests for the PDF report endpoint."""

from __future__ import annotations

import httpx
import pytest

from src.web.models import Simulation, SimulationMetrics, SimulationResult


def _sim() -> Simulation:
    return Simulation(
        name="report-test",
        lat=46.0,
        lon=8.9,
        tz="Europe/Rome",
        pv_power_kw=5.0,
        tilt=30.0,
        azimuth=180.0,
        inverter_power_kw=5.0,
        battery_capacity_kwh=10.0,
        battery_c_rate=0.5,
        annual_consumption_kwh=4000.0,
        purchase_eur_kwh=0.30,
        sell_eur_kwh=0.12,
        horizon_years=25,
        investment_cost_eur=12000.0,
        status="completed",
    )


def _result(simulation_id: int, year: int = 1) -> SimulationResult:
    return SimulationResult(
        simulation_id=simulation_id,
        year=year,
        pv_production_kwh=6000.0,
        load_consumption_kwh=4000.0,
        self_consumption_kwh=3000.0,
        self_consumption_pct=50.0,
        autosufficienza_pct=75.0,
        grid_export_kwh=3000.0,
        grid_import_kwh=1000.0,
        revenue_sold_eur=360.0,
        savings_self_consumption_eur=900.0,
        maintenance_cost_eur=0.0,
        replacement_cost_eur=0.0,
        grid_cost_eur=30.0,
        loan_payment_eur=0.0,
        net_cashflow_eur=1230.0,
        cumulative_cashflow_eur=1230.0,
    )


async def _seed_completed(db_session) -> int:
    sim = _sim()
    db_session.add(sim)
    await db_session.flush()
    db_session.add(
        SimulationMetrics(
            simulation_id=sim.id,
            npv_eur=1000.0,
            irr_pct=8.0,
            payback_years=12.0,
            total_autoconsumo_pct=50.0,
            total_autosufficienza_pct=75.0,
        )
    )
    db_session.add(_result(sim.id))
    await db_session.commit()
    return sim.id


@pytest.mark.asyncio()
async def test_report_not_found(logged_client: httpx.AsyncClient) -> None:
    resp = await logged_client.get("/api/simulations/999/report.pdf")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_report_pending_simulation_409(
    logged_client: httpx.AsyncClient,
) -> None:
    created = (
        await logged_client.post(
            "/api/simulations",
            json={
                "name": "pending",
                "lat": 46.0,
                "lon": 8.9,
                "tz": "Europe/Rome",
                "pv_power_kw": 5.0,
                "inverter_power_kw": 5.0,
                "annual_consumption_kwh": 4000.0,
                "purchase_eur_kwh": 0.30,
                "sell_eur_kwh": 0.12,
                "horizon_years": 25,
                "investment_cost_eur": 12000.0,
            },
        )
    ).json()
    resp = await logged_client.get(f"/api/simulations/{created['id']}/report.pdf")
    assert resp.status_code == 409


@pytest.mark.asyncio()
async def test_report_completed_pdf(
    db_session,
    logged_client: httpx.AsyncClient,
) -> None:
    sim_id = await _seed_completed(db_session)
    resp = await logged_client.get(f"/api/simulations/{sim_id}/report.pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"
