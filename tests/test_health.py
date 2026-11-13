"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness(client: AsyncClient):
    resp = await client.get("/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "ecommerce-api"
    assert "uptime_seconds" in data
    assert "metrics" in data
