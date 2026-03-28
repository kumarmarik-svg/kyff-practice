import hashlib
import hmac
from unittest.mock import MagicMock, patch

from app.models import Order, Payment
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from tests.conftest import SHIPPING_ADDR, auth

FAKE_RZ_ORDER_ID = "order_test_abc123"
FAKE_RZ_PAYMENT_ID = "pay_test_xyz789"


def _make_signature(key_secret: str, rz_order_id: str, rz_payment_id: str) -> str:
    payload = f"{rz_order_id}|{rz_payment_id}"
    return hmac.new(key_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _create_order(client, token, product):
    client.post("/api/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=auth(token),
    )
    res = client.post("/api/orders/",
        json={"shipping_address": SHIPPING_ADDR},
        headers=auth(token),
    )
    return res.get_json()["data"]["order_number"]


class TestCreatePayment:
    def test_create_payment_success(self, client, db, product, shipping_rule, user_token):
        order_number = _create_order(client, user_token, product)

        mock_rz_order = {"id": FAKE_RZ_ORDER_ID, "amount": 17000, "currency": "INR"}
        with patch("app.services.payment_service._client") as mock_client:
            mock_client.return_value.order.create.return_value = mock_rz_order
            res = client.post("/api/payments/create",
                json={"order_number": order_number},
                headers=auth(user_token),
            )

        assert res.status_code == 201
        data = res.get_json()["data"]
        assert data["razorpay_order_id"] == FAKE_RZ_ORDER_ID
        assert data["currency"] == "INR"

    def test_missing_order_number(self, client, user_token):
        res = client.post("/api/payments/create", json={}, headers=auth(user_token))
        assert res.status_code == 400

    def test_requires_auth(self, client):
        assert client.post("/api/payments/create", json={"order_number": "X"}).status_code == 401


class TestVerifyPayment:
    def test_verify_success(self, client, db, product, shipping_rule, user_token, app):
        order_number = _create_order(client, user_token, product)

        mock_rz_order = {"id": FAKE_RZ_ORDER_ID, "amount": 17000, "currency": "INR"}
        with patch("app.services.payment_service._client") as mock_client:
            mock_client.return_value.order.create.return_value = mock_rz_order
            client.post("/api/payments/create",
                json={"order_number": order_number},
                headers=auth(user_token),
            )

        key_secret = app.config["RAZORPAY_KEY_SECRET"]
        signature = _make_signature(key_secret, FAKE_RZ_ORDER_ID, FAKE_RZ_PAYMENT_ID)

        res = client.post("/api/payments/verify", json={
            "razorpay_order_id": FAKE_RZ_ORDER_ID,
            "razorpay_payment_id": FAKE_RZ_PAYMENT_ID,
            "razorpay_signature": signature,
        }, headers=auth(user_token))

        assert res.status_code == 200
        assert res.get_json()["data"]["status"] == "paid"

        # Order should be confirmed
        with app.app_context():
            order = Order.query.filter_by(order_number=order_number).first()
            assert order.status == OrderStatus.confirmed

    def test_invalid_signature(self, client, db, product, shipping_rule, user_token):
        order_number = _create_order(client, user_token, product)

        mock_rz_order = {"id": FAKE_RZ_ORDER_ID, "amount": 17000, "currency": "INR"}
        with patch("app.services.payment_service._client") as mock_client:
            mock_client.return_value.order.create.return_value = mock_rz_order
            client.post("/api/payments/create",
                json={"order_number": order_number},
                headers=auth(user_token),
            )

        res = client.post("/api/payments/verify", json={
            "razorpay_order_id": FAKE_RZ_ORDER_ID,
            "razorpay_payment_id": FAKE_RZ_PAYMENT_ID,
            "razorpay_signature": "badsignature",
        }, headers=auth(user_token))

        assert res.status_code == 400
        assert res.get_json()["message"] == "Invalid payment signature"

    def test_missing_fields(self, client, user_token):
        res = client.post("/api/payments/verify",
            json={"razorpay_order_id": "x"},
            headers=auth(user_token),
        )
        assert res.status_code == 400
