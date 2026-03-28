import re
from datetime import datetime, timezone

from app.extensions import db
from app.models import Cart, CartItem, Order, OrderItem, ProductVariant, ShippingRule
from app.models.order import OrderStatus


def _calc_shipping(subtotal: float, pincode: str) -> float:
    """Return flat_rate of first matching active rule ordered by priority DESC."""
    rules = ShippingRule.query.filter_by(is_active=True).order_by(ShippingRule.priority.desc()).all()
    for rule in rules:
        if rule.min_order_amount is not None and subtotal < float(rule.min_order_amount):
            continue
        if rule.max_order_amount is not None and subtotal > float(rule.max_order_amount):
            continue
        if rule.pincode_prefix and not pincode.startswith(rule.pincode_prefix):
            continue
        return float(rule.flat_rate)
    return 0.0


def _generate_order_number() -> str:
    year = datetime.now(timezone.utc).year
    last = (
        Order.query
        .filter(Order.order_number.like(f"KYFF-{year}%"))
        .order_by(Order.id.desc())
        .first()
    )
    if last:
        seq = int(re.search(r"\d+$", last.order_number).group()) + 1
    else:
        seq = 1
    return f"KYFF-{year}{seq:04d}"


def create_order(user_id: int | None, cart: Cart, shipping_address: dict, notes: str | None = None) -> Order:
    if not cart.items:
        raise ValueError("Cart is empty")

    # Build order items + calculate subtotal
    order_items = []
    subtotal = 0.0

    for cart_item in cart.items:
        product = cart_item.product
        if not product or not product.is_active:
            raise ValueError(f"Product '{product.name if product else cart_item.product_id}' is no longer available")

        variant = ProductVariant.query.get(cart_item.variant_id) if cart_item.variant_id else None

        # Stock check
        if variant:
            if variant.stock_qty < cart_item.quantity:
                raise ValueError(f"Insufficient stock for '{product.name} — {variant.name}'")
        else:
            if product.stock_qty < cart_item.quantity:
                raise ValueError(f"Insufficient stock for '{product.name}'")

        unit_price = float(cart_item.unit_price)
        total_price = unit_price * cart_item.quantity
        subtotal += total_price

        order_items.append(OrderItem(
            product_id=product.id,
            variant_id=variant.id if variant else None,
            product_name=product.name,
            variant_name=variant.name if variant else None,
            product_sku=variant.sku if variant else product.sku,
            quantity=cart_item.quantity,
            unit_price=unit_price,
            total_price=total_price,
        ))

    pincode = shipping_address.get("pincode", "")
    shipping_amount = _calc_shipping(subtotal, pincode)
    total_amount = subtotal + shipping_amount

    order = Order(
        order_number=_generate_order_number(),
        user_id=user_id,
        status=OrderStatus.pending,
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        total_amount=total_amount,
        shipping_address_snapshot=shipping_address,
        notes=notes,
    )
    db.session.add(order)
    db.session.flush()  # get order.id before adding items

    for item in order_items:
        item.order_id = order.id
        db.session.add(item)

    # Deduct stock
    for cart_item in cart.items:
        variant = ProductVariant.query.get(cart_item.variant_id) if cart_item.variant_id else None
        if variant:
            variant.stock_qty -= cart_item.quantity
        else:
            cart_item.product.stock_qty -= cart_item.quantity

    # Clear cart
    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()
    return order


def get_user_orders(user_id: int) -> list[Order]:
    return Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()


def get_order(order_number: str, user_id: int | None) -> Order:
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        raise ValueError("Order not found")
    if user_id and order.user_id != user_id:
        raise ValueError("Order not found")
    return order
