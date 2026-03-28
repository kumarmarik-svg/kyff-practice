from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.services import cart_service, order_service
from app.utils.decorators import jwt_required

orders_bp = Blueprint("orders", __name__)


def _item_dict(item):
    return {
        "id": item.id,
        "product_id": item.product_id,
        "variant_id": item.variant_id,
        "product_name": item.product_name,
        "variant_name": item.variant_name,
        "product_sku": item.product_sku,
        "quantity": item.quantity,
        "unit_price": str(item.unit_price),
        "total_price": str(item.total_price),
    }


def _order_dict(order, detail=False):
    d = {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "subtotal": str(order.subtotal),
        "discount_amount": str(order.discount_amount),
        "shipping_amount": str(order.shipping_amount),
        "tax_amount": str(order.tax_amount),
        "total_amount": str(order.total_amount),
        "tracking_number": order.tracking_number,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }
    if detail:
        d.update({
            "shipping_address": order.shipping_address_snapshot,
            "notes": order.notes,
            "items": [_item_dict(i) for i in order.items],
            "payment": _payment_dict(order.payment) if order.payment else None,
        })
    return d


def _payment_dict(payment):
    return {
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "amount_paise": payment.amount_paise,
        "currency": payment.currency,
        "status": payment.status.value,
        "method": payment.method,
    }


# POST /api/orders
@orders_bp.post("/")
@jwt_required
def create_order():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    shipping_address = data.get("shipping_address")
    if not shipping_address:
        return jsonify({"data": None, "message": "shipping_address required"}), 400

    required_addr = ("full_name", "phone", "line1", "city", "state", "pincode")
    missing = [f for f in required_addr if not shipping_address.get(f)]
    if missing:
        return jsonify({"data": None, "message": f"Missing address fields: {', '.join(missing)}"}), 400

    cart = cart_service.get_or_create_user_cart(user_id)

    try:
        order = order_service.create_order(
            user_id=user_id,
            cart=cart,
            shipping_address=shipping_address,
            notes=data.get("notes"),
        )
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 400

    return jsonify({"data": _order_dict(order, detail=True), "message": "Order created"}), 201


# GET /api/orders
@orders_bp.get("/")
@jwt_required
def list_orders():
    user_id = int(get_jwt_identity())
    orders = order_service.get_user_orders(user_id)
    return jsonify({"data": [_order_dict(o) for o in orders], "message": "OK"})


# GET /api/orders/<order_number>
@orders_bp.get("/<order_number>")
@jwt_required
def get_order(order_number):
    user_id = int(get_jwt_identity())
    try:
        order = order_service.get_order(order_number, user_id)
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 404
    return jsonify({"data": _order_dict(order, detail=True), "message": "OK"})
