from tests.conftest import auth

SESSION_KEY = "test-session-key-abc123"


class TestGuestCart:
    def test_get_empty_cart(self, client):
        res = client.get("/api/cart/", headers={"X-Session-Key": SESSION_KEY})
        assert res.status_code == 200
        assert res.get_json()["data"]["item_count"] == 0

    def test_no_session_key_returns_400(self, client):
        assert client.get("/api/cart/").status_code == 400

    def test_add_item(self, client, product):
        res = client.post("/api/cart/items",
            json={"product_id": product.id, "quantity": 2},
            headers={"X-Session-Key": SESSION_KEY},
        )
        assert res.status_code == 201
        data = res.get_json()["data"]
        assert data["item_count"] == 1
        assert data["items"][0]["quantity"] == 2

    def test_add_item_missing_product(self, client):
        res = client.post("/api/cart/items",
            json={"product_id": 9999, "quantity": 1},
            headers={"X-Session-Key": SESSION_KEY},
        )
        assert res.status_code == 400

    def test_update_item(self, client, product):
        client.post("/api/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"X-Session-Key": SESSION_KEY},
        )
        cart = client.get("/api/cart/", headers={"X-Session-Key": SESSION_KEY}).get_json()
        item_id = cart["data"]["items"][0]["id"]
        res = client.put(f"/api/cart/items/{item_id}",
            json={"quantity": 5},
            headers={"X-Session-Key": SESSION_KEY},
        )
        assert res.status_code == 200
        assert res.get_json()["data"]["items"][0]["quantity"] == 5

    def test_remove_item(self, client, product):
        client.post("/api/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"X-Session-Key": SESSION_KEY},
        )
        cart = client.get("/api/cart/", headers={"X-Session-Key": SESSION_KEY}).get_json()
        item_id = cart["data"]["items"][0]["id"]
        res = client.delete(f"/api/cart/items/{item_id}",
            headers={"X-Session-Key": SESSION_KEY},
        )
        assert res.status_code == 200
        assert res.get_json()["data"]["item_count"] == 0


class TestVariantCart:
    def test_add_variant_item(self, client, product_with_variant):
        p, v = product_with_variant
        res = client.post("/api/cart/items",
            json={"product_id": p.id, "variant_id": v.id, "quantity": 1},
            headers={"X-Session-Key": SESSION_KEY},
        )
        assert res.status_code == 201
        assert res.get_json()["data"]["items"][0]["variant_id"] == v.id

    def test_variant_required_for_has_variants_product(self, client, product_with_variant):
        p, _ = product_with_variant
        res = client.post("/api/cart/items",
            json={"product_id": p.id, "quantity": 1},
            headers={"X-Session-Key": SESSION_KEY},
        )
        assert res.status_code == 400

    def test_add_same_item_increments_quantity(self, client, product):
        headers = {"X-Session-Key": SESSION_KEY}
        client.post("/api/cart/items", json={"product_id": product.id, "quantity": 2}, headers=headers)
        client.post("/api/cart/items", json={"product_id": product.id, "quantity": 3}, headers=headers)
        cart = client.get("/api/cart/", headers=headers).get_json()
        assert cart["data"]["item_count"] == 1
        assert cart["data"]["items"][0]["quantity"] == 5


class TestUserCart:
    def test_user_cart_via_jwt(self, client, product, user_token):
        res = client.post("/api/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers=auth(user_token),
        )
        assert res.status_code == 201

    def test_merge_cart(self, client, product, user_token):
        # Add item to guest cart
        client.post("/api/cart/items",
            json={"product_id": product.id, "quantity": 3},
            headers={"X-Session-Key": "guest-merge-key"},
        )
        # Merge into user cart
        res = client.post("/api/cart/merge",
            json={"session_key": "guest-merge-key"},
            headers=auth(user_token),
        )
        assert res.status_code == 200
        assert res.get_json()["data"]["items"][0]["quantity"] == 3
