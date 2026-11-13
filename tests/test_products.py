"""Product API tests including CRUD, admin authorization, negative stock prevention, and audit event validation."""
import uuid
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
    assert resp.status_code == 422 or resp.status_code == 401


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    resp = await client.post(
        "/api/v1/products", json=SAMPLE_PRODUCT, headers=ADMIN_HEADERS
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "TEST-SKU-001"
    assert data["stock_quantity"] == 100
    assert "id" in data
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
async def test_adjust_stock_records_audit_event_with_custom_actor(client: AsyncClient):
    custom_admin_headers = {**ADMIN_HEADERS, "X-Admin-User": "lead.devops"}
    create_resp = await client.post(
        "/api/v1/products",
        json={**SAMPLE_PRODUCT, "sku": f"TEST-AUDIT-{uuid.uuid4().hex[:6]}", "stock_quantity": 20},
        headers=custom_admin_headers,
    )
    product_id = create_resp.json()["id"]

    # 1. Update product
    update_resp = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "Updated Test Widget", "price": "29.99"},
        headers=custom_admin_headers,
    )
    assert update_resp.status_code == 200

    # 2. Adjust stock
    adj_resp = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"quantity_delta": 15, "reason": "Restocked warehouse"},
        headers=custom_admin_headers,
    )
    assert adj_resp.status_code == 200
    assert adj_resp.json()["stock_quantity"] == 35

    # 3. Check audit history requires admin authentication
    unauth_resp = await client.get(f"/api/v1/products/{product_id}/audit")
    assert unauth_resp.status_code in (401, 422)

    # 4. Check audit history with admin credentials
    audit_resp = await client.get(
        f"/api/v1/products/{product_id}/audit",
        headers=custom_admin_headers,
    )
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 3  # create_product, update_product, adjust_stock

    # Verify that the entity_id in the audit record matches the actual product ID
    creation_event = next(e for e in events if e["action"] == "create_product")
    assert creation_event["entity_id"] == str(product_id)
    assert creation_event["actor"] == "lead.devops"

    update_event = next(e for e in events if e["action"] == "update_product")
    assert update_event["entity_id"] == str(product_id)
    assert update_event["actor"] == "lead.devops"
