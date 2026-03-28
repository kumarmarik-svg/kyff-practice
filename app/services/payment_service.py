import hashlib
import hmac

import razorpay
from flask import current_app

from app.extensions import db
from app.models import Order, Payment
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus


def _client() -> razorpay.Client:
    return razorpay.Client(auth=(
        current_app.config["RAZORPAY_KEY_ID"],
        current_app.config["RAZORPAY_KEY_SECRET"],
    ))


def create_razorpay_order(order: Order) -> Payment:
    if order.payment:
        raise ValueError("Payment already initiated for this order")

    amount_paise = int(float(order.total_amount) * 100)
    rz_order = _client().order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": order.order_number,
    })

    payment = Payment(
        order_id=order.id,
        razorpay_order_id=rz_order["id"],
        amount_paise=amount_paise,
        status=PaymentStatus.created,
    )
    db.session.add(payment)
    db.session.commit()
    return payment


def verify_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Payment:
    payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not payment:
        raise ValueError("Payment record not found")

    # HMAC-SHA256 verification
    payload = f"{razorpay_order_id}|{razorpay_payment_id}"
    secret = current_app.config["RAZORPAY_KEY_SECRET"].encode("utf-8")
    expected = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, razorpay_signature):
        payment.status = PaymentStatus.failed
        payment.failure_reason = "Signature verification failed"
        db.session.commit()
        raise ValueError("Invalid payment signature")

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = PaymentStatus.paid

    order = Order.query.get(payment.order_id)
    order.status = OrderStatus.confirmed

    db.session.commit()
    return payment
