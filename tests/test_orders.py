from tests.conftest import SHIPPING_ADDR, auth


def _add_to_cart(client, token, product_id, quantity=1):
    client.post("/api/cart/items",
        json={"product_id": product_id, "quantity": quantity},
        headers=auth(token),
    )


class TestCreateOrder:
    def test_create_order_success(self, client, product, shipping_rule, user_token):
        _add_to_cart(client, user_token, product.id, 2)
        res = client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        assert res.status_code == 201
        data = res.get_json()["data"]
        assert data["order_number"].startswith("KYFF-")
        assert data["status"] == "pending"
        assert float(data["shipping_amount"]) == 50.0
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2

    def test_cart_cleared_after_order(self, client, product, shipping_rule, user_token):
        _add_to_cart(client, user_token, product.id)
        client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        cart = client.get("/api/cart/", headers=auth(user_token)).get_json()
        assert cart["data"]["item_count"] == 0

    def test_stock_deducted(self, client, db, product, shipping_rule, user_token):
        initial_stock = product.stock_qty
        _add_to_cart(client, user_token, product.id, 3)
        client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        db.session.refresh(product)
        assert product.stock_qty == initial_stock - 3

    def test_empty_cart_returns_400(self, client, user_token):
        res = client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        assert res.status_code == 400

    def test_missing_shipping_address(self, client, product, user_token):
        _add_to_cart(client, user_token, product.id)
        res = client.post("/api/orders/", json={}, headers=auth(user_token))
        assert res.status_code == 400

    def test_requires_auth(self, client):
        assert client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}).status_code == 401

    def test_order_number_sequential(self, client, db, product, shipping_rule, user_token):
        _add_to_cart(client, user_token, product.id)
        res1 = client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        _add_to_cart(client, user_token, product.id)
        res2 = client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        n1 = res1.get_json()["data"]["order_number"]
        n2 = res2.get_json()["data"]["order_number"]
        assert n1 != n2
        assert int(n2[-4:]) == int(n1[-4:]) + 1


class TestListAndGetOrders:
    def test_list_orders(self, client, product, shipping_rule, user_token):
        _add_to_cart(client, user_token, product.id)
        client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        res = client.get("/api/orders/", headers=auth(user_token))
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 1

    def test_get_order_by_number(self, client, product, shipping_rule, user_token):
        _add_to_cart(client, user_token, product.id)
        create_res = client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        order_number = create_res.get_json()["data"]["order_number"]
        res = client.get(f"/api/orders/{order_number}", headers=auth(user_token))
        assert res.status_code == 200
        assert res.get_json()["data"]["order_number"] == order_number

    def test_get_other_users_order_returns_404(self, client, db, product, shipping_rule, user_token, admin_token):
        _add_to_cart(client, user_token, product.id)
        create_res = client.post("/api/orders/", json={"shipping_address": SHIPPING_ADDR}, headers=auth(user_token))
        order_number = create_res.get_json()["data"]["order_number"]
        res = client.get(f"/api/orders/{order_number}", headers=auth(admin_token))
        assert res.status_code == 404
