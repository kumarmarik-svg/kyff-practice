from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models import OrderItem, Product, Review
from app.utils.decorators import jwt_required

reviews_bp = Blueprint("reviews", __name__)


def _review_dict(r):
    return {
        "id": r.id,
        "product_id": r.product_id,
        "user_id": r.user_id,
        "rating": r.rating,
        "title": r.title,
        "body": r.body,
        "is_verified_purchase": r.is_verified_purchase,
        "is_approved": r.is_approved,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# POST /api/reviews
@reviews_bp.post("/")
@jwt_required
def create_review():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    if not data.get("product_id"):
        return jsonify({"data": None, "message": "product_id required"}), 400
    if not data.get("rating") or not (1 <= int(data["rating"]) <= 5):
        return jsonify({"data": None, "message": "rating must be 1–5"}), 400

    product = Product.query.get(data["product_id"])
    if not product or not product.is_active:
        return jsonify({"data": None, "message": "Product not found"}), 404

    if Review.query.filter_by(product_id=product.id, user_id=user_id).first():
        return jsonify({"data": None, "message": "You have already reviewed this product"}), 409

    # Verified purchase check
    is_verified = False
    order_item_id = data.get("order_item_id")
    if order_item_id:
        order_item = OrderItem.query.get(order_item_id)
        if (
            order_item
            and order_item.product_id == product.id
            and order_item.order
            and order_item.order.user_id == user_id
        ):
            is_verified = True
        else:
            order_item_id = None  # ignore invalid order_item_id silently

    review = Review(
        product_id=product.id,
        user_id=user_id,
        order_item_id=order_item_id,
        rating=int(data["rating"]),
        title=data.get("title"),
        body=data.get("body"),
        is_verified_purchase=is_verified,
        is_approved=False,
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"data": _review_dict(review), "message": "Review submitted and pending approval"}), 201


# PUT /api/reviews/<id>
@reviews_bp.put("/<int:review_id>")
@jwt_required
def update_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query.filter_by(id=review_id, user_id=user_id).first()
    if not review:
        return jsonify({"data": None, "message": "Review not found"}), 404

    data = request.get_json(silent=True) or {}

    if "rating" in data:
        if not (1 <= int(data["rating"]) <= 5):
            return jsonify({"data": None, "message": "rating must be 1–5"}), 400
        review.rating = int(data["rating"])
    for field in ("title", "body"):
        if field in data:
            setattr(review, field, data[field])

    # Reset approval on edit
    review.is_approved = False
    db.session.commit()
    return jsonify({"data": _review_dict(review), "message": "Review updated and pending re-approval"})


# DELETE /api/reviews/<id>
@reviews_bp.delete("/<int:review_id>")
@jwt_required
def delete_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query.filter_by(id=review_id, user_id=user_id).first()
    if not review:
        return jsonify({"data": None, "message": "Review not found"}), 404

    db.session.delete(review)
    db.session.commit()
    return jsonify({"data": None, "message": "Review deleted"})
