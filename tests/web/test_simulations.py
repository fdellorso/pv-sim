"""Tests for the simulations API."""

from __future__ import annotations

import httpx
import pytest

_PAYLOAD = {
    "name": "test",
    "lat": 46.0,
    "lon": 8.9,
    "tz": "Europe/Rome",
    "pv_power_kw": 5.0,
    "tilt": 30.0,
    "azimuth": 180.0,
    "inverter_power_kw": 5.0,
    "annual_consumption_kwh": 4000.0,
    "purchase_eur_kwh": 0.30,
    "sell_eur_kwh": 0.12,
    "horizon_years": 25,
    "investment_cost_eur": 12000.0,
}


@pytest.mark.asyncio()
async def test_create_simulation_enqueues_job(logged_client: httpx.AsyncClient, fake_arq) -> None:
    resp = await logged_client.post("/api/simulations", json=_PAYLOAD)
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert "run_simulation" in [name for name, _ in fake_arq.enqueued]


@pytest.mark.asyncio()
async def test_create_requires_load_source(logged_client: httpx.AsyncClient) -> None:
    payload = {k: v for k, v in _PAYLOAD.items() if k not in ("annual_consumption_kwh",)}
    resp = await logged_client.post("/api/simulations", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio()
async def test_get_simulation_not_found(logged_client: httpx.AsyncClient) -> None:
    resp = await logged_client.get("/api/simulations/999")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_created_simulation_roundtrip(
    logged_client: httpx.AsyncClient,
) -> None:
    created = (await logged_client.post("/api/simulations", json=_PAYLOAD)).json()
    resp = await logged_client.get(f"/api/simulations/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "queued"
    assert body["name"] == "test"
    assert body["metrics"] is None
    assert body["results"] is None


@pytest.mark.asyncio()
async def test_invalid_battery_params_rejected(logged_client: httpx.AsyncClient) -> None:
    payload = dict(_PAYLOAD)
    payload["pv_power_kw"] = -5.0
    resp = await logged_client.post("/api/simulations", json=payload)
    assert resp.status_code == 422
