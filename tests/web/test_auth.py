"""Tests for single-password auth and the session middleware."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio()
async def test_login_page(client: httpx.AsyncClient) -> None:
    resp = await client.get("/login")
    assert resp.status_code == 200


@pytest.mark.asyncio()
async def test_login_wrong_password(client: httpx.AsyncClient) -> None:
    resp = await client.post("/login", data={"password": "wrong"})
    assert resp.status_code == 303
    assert resp.headers["location"].endswith("/login?error=1")


@pytest.mark.asyncio()
async def test_login_right_password(client: httpx.AsyncClient) -> None:
    resp = await client.post("/login", data={"password": "test-password"})
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"


@pytest.mark.asyncio()
async def test_unauth_page_redirects_to_login(client: httpx.AsyncClient) -> None:
    resp = await client.get("/new")
    assert resp.status_code == 303
    assert "/login?next=/new" in resp.headers["location"]


@pytest.mark.asyncio()
async def test_unauth_api_returns_401(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/simulations/1")
    assert resp.status_code == 401


@pytest.mark.asyncio()
async def test_logout_clears_session(logged_client: httpx.AsyncClient) -> None:
    resp = await logged_client.post("/logout")
    assert resp.status_code == 303
    # after logout the page requires auth again
    resp2 = await logged_client.get("/new")
    assert resp2.status_code == 303
