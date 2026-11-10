"""Order API tests including idempotency."""
import uuid
import pytest
from httpx import AsyncClient

from tests.conftest import ADMIN_HEADERS

PRODUCT_PAYLOAD = {
    "sku": "ORDER-TEST-PROD",
    "name": "Order Test Product",
    "price": "50.00",
    "stock_quantity": 20,
    "is_active": True,
}


async def _create_product(client: AsyncClient, sku: str = None, stock: int = 20) -> dict:
    payload = {**PRODUCT_PAYLOAD, "stock_quantity": stock}
    if sku:
        payload["sku"] = sku
    resp = await client.post("/api/v1/products", json=payload, headers=ADMIN_HEADERS)
    if resp.status_code not in (200, 201):
        search = await client.get(f"/api/v1/products?q={payload['sku']}")
        return search.json()["items"][0]
    return resp.json()


@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient):
    product = await _create_product(client, sku=f"ORD-PROD-{uuid.uuid4().hex[:6]}")
    idem_key = f"idem-{uuid.uuid4()}"
    resp = await client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": idem_key,
            "customer_email": "test@example.com",
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "confirmed"
    assert float(data["total_amount"]) == 100.0
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_order_idempotency(client: AsyncClient):
    """Submitting the same idempotency key twice must not duplicate the order or deduct stock twice."""
    product = await _create_product(client, sku=f"IDEM-PROD-{uuid.uuid4().hex[:6]}", stock=10)
    idem_key = f"idem-{uuid.uuid4()}"
    order_payload = {
        "idempotency_key": idem_key,
        "customer_email": "idem@example.com",
        "items": [{"product_id": product["id"], "quantity": 2}],
    }

    resp1 = await client.post("/api/v1/orders", json=order_payload)
    assert resp1.status_code == 201
    order_id_1 = resp1.json()["id"]

    resp2 = await client.post("/api/v1/orders", json=order_payload)
    assert resp2.status_code == 201
    order_id_2 = resp2.json()["id"]

    assert order_id_1 == order_id_2

    prod_resp = await client.get(f"/api/v1/products/{product['id']}")
    assert prod_resp.json()["stock_quantity"] == 8  # 10 - 2 (not 10 - 4)


@pytest.mark.asyncio
async def test_order_insufficient_stock(client: AsyncClient):
    product = await _create_product(client, sku=f"LOW-STOCK-{uuid.uuid4().hex[:6]}", stock=1)
    resp = await client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": f"idem-{uuid.uuid4()}",
            "customer_email": "fail@example.com",
            "items": [{"product_id": product["id"], "quantity": 999}],
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_order_status(client: AsyncClient):
    product = await _create_product(client, sku=f"STATUS-PROD-{uuid.uuid4().hex[:6]}")
    idem_key = f"idem-{uuid.uuid4()}"
    create_resp = await client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": idem_key,
            "customer_email": "status@example.com",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    )
    order_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id
