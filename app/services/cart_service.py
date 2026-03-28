from app.extensions import db
from app.models import Cart, CartItem, Product, ProductVariant


def _get_price(product, variant):
    if variant:
        return variant.sale_price if variant.sale_price else variant.price
    return product.sale_price if product.sale_price else product.base_price


def get_or_create_user_cart(user_id: int) -> Cart:
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


def get_or_create_guest_cart(session_key: str) -> Cart:
    cart = Cart.query.filter_by(session_key=session_key).first()
    if not cart:
        cart = Cart(session_key=session_key)
        db.session.add(cart)
        db.session.commit()
    return cart


def get_cart(cart: Cart) -> dict:
    items = []
    subtotal = 0
    for item in cart.items:
        variant = ProductVariant.query.get(item.variant_id) if item.variant_id else None
        line_total = float(item.unit_price) * item.quantity
        subtotal += line_total
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "variant_id": item.variant_id,
            "variant_name": variant.name if variant else None,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "line_total": f"{line_total:.2f}",
        })
    return {"items": items, "subtotal": f"{subtotal:.2f}", "item_count": len(items)}


def add_item(cart: Cart, product_id: int, quantity: int, variant_id: int | None) -> CartItem:
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        raise ValueError("Product not found")

    variant = None
    if variant_id:
        variant = ProductVariant.query.get(variant_id)
        if not variant or variant.product_id != product_id or not variant.is_active:
            raise ValueError("Variant not found")

    if product.has_variants and not variant:
        raise ValueError("This product requires a variant selection")

    unit_price = _get_price(product, variant)

    # If item exists, increment quantity
    existing = CartItem.query.filter_by(
        cart_id=cart.id, product_id=product_id, variant_id=variant_id
    ).first()
    if existing:
        existing.quantity += quantity
        existing.unit_price = unit_price  # refresh price snapshot
        db.session.commit()
        return existing

    item = CartItem(
        cart_id=cart.id,
        product_id=product_id,
        variant_id=variant_id,
        quantity=quantity,
        unit_price=unit_price,
    )
    db.session.add(item)
    db.session.commit()
    return item


def update_item(cart: Cart, item_id: int, quantity: int) -> CartItem:
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        raise ValueError("Cart item not found")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    item.quantity = quantity
    db.session.commit()
    return item


def remove_item(cart: Cart, item_id: int) -> None:
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        raise ValueError("Cart item not found")
    db.session.delete(item)
    db.session.commit()


def merge_guest_cart(user_id: int, session_key: str) -> Cart:
    """Merge guest cart into user cart on login. Guest cart is deleted after merge."""
    guest_cart = Cart.query.filter_by(session_key=session_key).first()
    if not guest_cart:
        return get_or_create_user_cart(user_id)

    user_cart = get_or_create_user_cart(user_id)

    for guest_item in list(guest_cart.items):
        existing = CartItem.query.filter_by(
            cart_id=user_cart.id,
            product_id=guest_item.product_id,
            variant_id=guest_item.variant_id,
        ).first()
        if existing:
            existing.quantity += guest_item.quantity
        else:
            db.session.add(CartItem(
                cart_id=user_cart.id,
                product_id=guest_item.product_id,
                variant_id=guest_item.variant_id,
                quantity=guest_item.quantity,
                unit_price=guest_item.unit_price,
            ))

    db.session.delete(guest_cart)
    db.session.commit()
    return user_cart
