"""Tests for the load profile upload API."""

from __future__ import annotations

import httpx
import pytest

_VALID_CSV = (
    "timestamp,power_kw\n"
    "2020-01-01 00:00:00,1.0\n"
    "2020-01-01 00:15:00,2.0\n"
    "2020-01-01 00:30:00,3.0\n"
)


async def _upload(
    client: httpx.AsyncClient, content: str, filename: str = "curve.csv"
) -> httpx.Response:
    return await client.post(
        "/api/load-profiles/upload",
        files={"file": (filename, content.encode(), "text/csv")},
    )


@pytest.mark.asyncio()
async def test_upload_valid_csv(logged_client: httpx.AsyncClient) -> None:
    resp = await _upload(logged_client, _VALID_CSV)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "curve"
    assert body["annual_consumption_kwh"] == pytest.approx(6.0 * 0.25)


@pytest.mark.asyncio()
async def test_upload_rejects_non_csv(logged_client: httpx.AsyncClient) -> None:
    resp = await _upload(logged_client, _VALID_CSV, filename="curve.txt")
    assert resp.status_code == 400
    assert "Only CSV files" in resp.json()["detail"]


@pytest.mark.asyncio()
async def test_upload_rejects_empty_file(logged_client: httpx.AsyncClient) -> None:
    resp = await _upload(logged_client, "")
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"]


@pytest.mark.asyncio()
async def test_upload_rejects_missing_power_kw(logged_client: httpx.AsyncClient) -> None:
    csv = "timestamp,consumo_kw\n2020-01-01 00:00:00,0.5\n"
    resp = await _upload(logged_client, csv)
    assert resp.status_code == 400
    assert "timestamp" in resp.json()["detail"]


@pytest.mark.asyncio()
async def test_upload_rejects_missing_timestamp(logged_client: httpx.AsyncClient) -> None:
    csv = "power_kw\n0.5\n"
    resp = await _upload(logged_client, csv)
    assert resp.status_code == 400
    assert "timestamp" in resp.json()["detail"]


@pytest.mark.asyncio()
async def test_upload_rejects_malformed_csv(logged_client: httpx.AsyncClient) -> None:
    csv = "questo non è un csv valido,power_kw\nriga senza senso\n"
    resp = await _upload(logged_client, csv)
    assert resp.status_code == 400
    assert "power_kw" in resp.json()["detail"]


@pytest.mark.asyncio()
async def test_upload_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await _upload(client, _VALID_CSV)
    assert resp.status_code == 401
