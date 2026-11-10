"""Product API tests."""
import pytest
from httpx import AsyncClient

from tests.conftest import ADMIN_HEADERS

SAMPLE_PRODUCT = {
    "sku": "TEST-SKU-001",
    "name": "Test Widget",
    "description": "A test product",
    "price": "19.99",
    "stock_quantity": 100,
    "is_active": True,
}


@pytest.mark.asyncio
async def test_create_product_requires_admin(client: AsyncClient):
    resp = await client.post("/api/v1/products", json=SAMPLE_PRODUCT)
    assert resp.status_code == 422  # missing X-API-Key header


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    resp = await client.post(
        "/api/v1/products", json=SAMPLE_PRODUCT, headers=ADMIN_HEADERS
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "TEST-SKU-001"
    assert data["stock_quantity"] == 100
    return data


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    await client.post("/api/v1/products", json=SAMPLE_PRODUCT, headers=ADMIN_HEADERS)
    resp = await client.get("/api/v1/products")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient):
    await client.post("/api/v1/products", json=SAMPLE_PRODUCT, headers=ADMIN_HEADERS)
    resp = await client.get("/api/v1/products?q=Widget")
    assert resp.status_code == 200
    data = resp.json()
    assert any("Widget" in p["name"] for p in data["items"])


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_adjust_stock_prevents_negative(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/products", json={**SAMPLE_PRODUCT, "sku": "TEST-NEG-STOCK", "stock_quantity": 5},
        headers=ADMIN_HEADERS,
    )
    product_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"quantity_delta": -10, "reason": "test negative"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_adjust_stock_records_audit_event(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/products", json={**SAMPLE_PRODUCT, "sku": "TEST-AUDIT-SKU", "stock_quantity": 20},
        headers=ADMIN_HEADERS,
    )
    product_id = create_resp.json()["id"]

    # Valid stock adjustment
    adj_resp = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"quantity_delta": 15, "reason": "Restocked inventory"},
        headers=ADMIN_HEADERS,
    )
    assert adj_resp.status_code == 200
    assert adj_resp.json()["stock_quantity"] == 35

    # Check audit history
    audit_resp = await client.get(
        f"/api/v1/products/{product_id}/audit",
        headers=ADMIN_HEADERS,
    )
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 2  # create_product and adjust_stock
    assert any(e["action"] == "adjust_stock" for e in events)
