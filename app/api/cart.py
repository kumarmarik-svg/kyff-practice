from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.services import cart_service

cart_bp = Blueprint("cart", __name__)


def _resolve_cart():
    """Return the cart for the current user (JWT) or guest (session_key header)."""
    try:
        verify_jwt_in_request(optional=True)
        user_id = int(get_jwt_identity())
    except Exception:
        user_id = None

    if user_id:
        return cart_service.get_or_create_user_cart(user_id)

    session_key = request.headers.get("X-Session-Key") or request.args.get("session_key")
    if not session_key:
        return None
    return cart_service.get_or_create_guest_cart(session_key)


# GET /api/cart
@cart_bp.get("/")
def get_cart():
    cart = _resolve_cart()
    if not cart:
        return jsonify({"data": None, "message": "Session key required for guest cart"}), 400
    return jsonify({"data": cart_service.get_cart(cart), "message": "OK"})


# POST /api/cart/items
@cart_bp.post("/items")
def add_item():
    cart = _resolve_cart()
    if not cart:
        return jsonify({"data": None, "message": "Session key required for guest cart"}), 400

    data = request.get_json(silent=True) or {}
    if not data.get("product_id"):
        return jsonify({"data": None, "message": "product_id required"}), 400

    try:
        cart_service.add_item(
            cart,
            product_id=int(data["product_id"]),
            quantity=max(1, int(data.get("quantity", 1))),
            variant_id=data.get("variant_id"),
        )
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 400

    return jsonify({"data": cart_service.get_cart(cart), "message": "Item added"}), 201


# PUT /api/cart/items/<id>
@cart_bp.put("/items/<int:item_id>")
def update_item(item_id):
    cart = _resolve_cart()
    if not cart:
        return jsonify({"data": None, "message": "Session key required for guest cart"}), 400

    data = request.get_json(silent=True) or {}
    if "quantity" not in data:
        return jsonify({"data": None, "message": "quantity required"}), 400

    try:
        cart_service.update_item(cart, item_id, int(data["quantity"]))
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 400

    return jsonify({"data": cart_service.get_cart(cart), "message": "Item updated"})


# DELETE /api/cart/items/<id>
@cart_bp.delete("/items/<int:item_id>")
def remove_item(item_id):
    cart = _resolve_cart()
    if not cart:
        return jsonify({"data": None, "message": "Session key required for guest cart"}), 400

    try:
        cart_service.remove_item(cart, item_id)
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 404

    return jsonify({"data": cart_service.get_cart(cart), "message": "Item removed"})


# POST /api/cart/merge
@cart_bp.post("/merge")
def merge_cart():
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"data": None, "message": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    session_key = data.get("session_key") or request.headers.get("X-Session-Key")
    if not session_key:
        return jsonify({"data": None, "message": "session_key required"}), 400

    cart = cart_service.merge_guest_cart(user_id, session_key)
    return jsonify({"data": cart_service.get_cart(cart), "message": "Cart merged"})
