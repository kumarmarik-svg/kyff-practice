from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.services import order_service, payment_service
from app.utils.decorators import jwt_required

payments_bp = Blueprint("payments", __name__)


# POST /api/payments/create
@payments_bp.post("/create")
@jwt_required
def create_payment():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    order_number = data.get("order_number")
    if not order_number:
        return jsonify({"data": None, "message": "order_number required"}), 400

    try:
        order = order_service.get_order(order_number, user_id)
        payment = payment_service.create_razorpay_order(order)
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 400

    return jsonify({
        "data": {
            "razorpay_order_id": payment.razorpay_order_id,
            "amount_paise": payment.amount_paise,
            "currency": payment.currency,
            "order_number": order.order_number,
        },
        "message": "Payment initiated",
    }), 201


# POST /api/payments/verify
@payments_bp.post("/verify")
@jwt_required
def verify_payment():
    data = request.get_json(silent=True) or {}

    required = ("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"data": None, "message": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        payment = payment_service.verify_payment(
            data["razorpay_order_id"],
            data["razorpay_payment_id"],
            data["razorpay_signature"],
        )
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 400

    return jsonify({
        "data": {
            "status": payment.status.value,
            "razorpay_payment_id": payment.razorpay_payment_id,
        },
        "message": "Payment verified successfully",
    })
