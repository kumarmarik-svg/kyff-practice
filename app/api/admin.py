from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Banner, Order, Product, ProductImage, ProductVariant, Review, ShippingRule, User
from app.models.order import OrderStatus
from app.services import admin_service
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _product_dict(p):
    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "sku": p.sku,
        "category_id": p.category_id,
        "base_price": str(p.base_price),
        "sale_price": str(p.sale_price) if p.sale_price else None,
        "cost_price": str(p.cost_price) if p.cost_price else None,
        "stock_qty": p.stock_qty,
        "low_stock_threshold": p.low_stock_threshold,
        "has_variants": p.has_variants,
        "is_active": p.is_active,
        "is_featured": p.is_featured,
        "is_organic_certified": p.is_organic_certified,
        "tags": p.tags,
        "weight_grams": p.weight_grams,
        "variants": [_variant_dict(v) for v in p.variants],
        "images": [_image_dict(i) for i in p.images],
    }


def _variant_dict(v):
    return {
        "id": v.id, "name": v.name, "sku": v.sku,
        "price": str(v.price), "sale_price": str(v.sale_price) if v.sale_price else None,
        "stock_qty": v.stock_qty, "is_active": v.is_active, "sort_order": v.sort_order,
    }


def _image_dict(i):
    return {"id": i.id, "url": i.url, "alt_text": i.alt_text, "sort_order": i.sort_order, "is_primary": i.is_primary}


def _order_dict(o):
    return {
        "id": o.id, "order_number": o.order_number,
        "user_id": o.user_id, "guest_email": o.guest_email,
        "status": o.status.value,
        "subtotal": str(o.subtotal), "shipping_amount": str(o.shipping_amount),
        "total_amount": str(o.total_amount),
        "tracking_number": o.tracking_number,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _user_dict(u):
    return {
        "id": u.id, "email": u.email,
        "first_name": u.first_name, "last_name": u.last_name,
        "phone": u.phone, "is_admin": u.is_admin,
        "is_active": u.is_active, "email_verified": u.email_verified,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def _review_dict(r):
    return {
        "id": r.id, "product_id": r.product_id, "user_id": r.user_id,
        "rating": r.rating, "title": r.title, "body": r.body,
        "is_approved": r.is_approved, "is_verified_purchase": r.is_verified_purchase,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _banner_dict(b):
    return {
        "id": b.id, "title": b.title, "subtitle": b.subtitle,
        "image_url": b.image_url, "link_url": b.link_url, "link_text": b.link_text,
        "position": b.position, "is_active": b.is_active, "sort_order": b.sort_order,
        "starts_at": b.starts_at.isoformat() if b.starts_at else None,
        "ends_at": b.ends_at.isoformat() if b.ends_at else None,
    }


def _shipping_dict(r):
    return {
        "id": r.id, "name": r.name,
        "min_order_amount": str(r.min_order_amount) if r.min_order_amount is not None else None,
        "max_order_amount": str(r.max_order_amount) if r.max_order_amount is not None else None,
        "flat_rate": str(r.flat_rate), "pincode_prefix": r.pincode_prefix,
        "is_active": r.is_active, "priority": r.priority,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    return jsonify({"data": admin_service.get_dashboard_stats(), "message": "OK"})


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@admin_bp.get("/products")
@admin_required
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    pagination = Product.query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"data": {
        "items": [_product_dict(p) for p in pagination.items],
        "total": pagination.total, "page": page, "pages": pagination.pages,
    }, "message": "OK"})


@admin_bp.post("/products")
@admin_required
def create_product():
    data = request.get_json(silent=True) or {}
    required = ("name", "slug", "sku", "category_id", "base_price")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"data": None, "message": f"Missing fields: {', '.join(missing)}"}), 400

    product = Product(
        category_id=data["category_id"], name=data["name"], slug=data["slug"],
        description=data.get("description"), short_description=data.get("short_description"),
        base_price=data["base_price"], sale_price=data.get("sale_price"),
        cost_price=data.get("cost_price"), sku=data["sku"],
        stock_qty=data.get("stock_qty", 0), low_stock_threshold=data.get("low_stock_threshold", 5),
        has_variants=data.get("has_variants", False), weight_grams=data.get("weight_grams"),
        is_active=data.get("is_active", True), is_featured=data.get("is_featured", False),
        is_organic_certified=data.get("is_organic_certified", False),
        tags=data.get("tags"), meta_title=data.get("meta_title"),
        meta_description=data.get("meta_description"),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"data": _product_dict(product), "message": "Product created"}), 201


@admin_bp.put("/products/<int:product_id>")
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json(silent=True) or {}
    updatable = (
        "name", "slug", "description", "short_description", "base_price", "sale_price",
        "cost_price", "sku", "stock_qty", "low_stock_threshold", "has_variants",
        "weight_grams", "is_active", "is_featured", "is_organic_certified",
        "tags", "meta_title", "meta_description", "category_id",
    )
    for field in updatable:
        if field in data:
            setattr(product, field, data[field])
    db.session.commit()
    return jsonify({"data": _product_dict(product), "message": "Product updated"})


@admin_bp.delete("/products/<int:product_id>")
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"data": None, "message": "Product deleted"})


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

VALID_STATUSES = {s.value for s in OrderStatus}


@admin_bp.get("/orders")
@admin_required
def list_orders():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status = request.args.get("status")
    q = Order.query
    if status:
        q = q.filter(Order.status == status)
    pagination = q.order_by(Order.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"data": {
        "items": [_order_dict(o) for o in pagination.items],
        "total": pagination.total, "page": page, "pages": pagination.pages,
    }, "message": "OK"})


@admin_bp.put("/orders/<int:order_id>/status")
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if not status or status not in VALID_STATUSES:
        return jsonify({"data": None, "message": f"Valid statuses: {', '.join(VALID_STATUSES)}"}), 400
    if data.get("tracking_number"):
        order.tracking_number = data["tracking_number"]
    order.status = status
    db.session.commit()
    return jsonify({"data": _order_dict(order), "message": "Order status updated"})


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@admin_bp.get("/users")
@admin_required
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    pagination = User.query.order_by(User.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"data": {
        "items": [_user_dict(u) for u in pagination.items],
        "total": pagination.total, "page": page, "pages": pagination.pages,
    }, "message": "OK"})


@admin_bp.put("/users/<int:user_id>/toggle-active")
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"data": _user_dict(user), "message": f"User {'activated' if user.is_active else 'deactivated'}"})


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@admin_bp.get("/reviews")
@admin_required
def list_reviews():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    approved = request.args.get("approved")
    q = Review.query
    if approved is not None:
        q = q.filter_by(is_approved=(approved.lower() == "true"))
    pagination = q.order_by(Review.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"data": {
        "items": [_review_dict(r) for r in pagination.items],
        "total": pagination.total, "page": page, "pages": pagination.pages,
    }, "message": "OK"})


@admin_bp.put("/reviews/<int:review_id>/approve")
@admin_required
def approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    db.session.commit()
    return jsonify({"data": _review_dict(review), "message": "Review approved"})


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------

@admin_bp.get("/banners")
@admin_required
def list_banners():
    banners = Banner.query.order_by(Banner.sort_order).all()
    return jsonify({"data": [_banner_dict(b) for b in banners], "message": "OK"})


@admin_bp.post("/banners")
@admin_required
def create_banner():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("image_url"):
        return jsonify({"data": None, "message": "title and image_url required"}), 400
    banner = Banner(
        title=data["title"], subtitle=data.get("subtitle"),
        image_url=data["image_url"], link_url=data.get("link_url"),
        link_text=data.get("link_text"), position=data.get("position"),
        is_active=data.get("is_active", True), sort_order=data.get("sort_order", 0),
        starts_at=data.get("starts_at"), ends_at=data.get("ends_at"),
    )
    db.session.add(banner)
    db.session.commit()
    return jsonify({"data": _banner_dict(banner), "message": "Banner created"}), 201


@admin_bp.put("/banners/<int:banner_id>")
@admin_required
def update_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    data = request.get_json(silent=True) or {}
    for field in ("title", "subtitle", "image_url", "link_url", "link_text", "position", "is_active", "sort_order", "starts_at", "ends_at"):
        if field in data:
            setattr(banner, field, data[field])
    db.session.commit()
    return jsonify({"data": _banner_dict(banner), "message": "Banner updated"})


@admin_bp.delete("/banners/<int:banner_id>")
@admin_required
def delete_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    return jsonify({"data": None, "message": "Banner deleted"})


# ---------------------------------------------------------------------------
# Shipping Rules
# ---------------------------------------------------------------------------

@admin_bp.get("/shipping-rules")
@admin_required
def list_shipping_rules():
    rules = ShippingRule.query.order_by(ShippingRule.priority.desc()).all()
    return jsonify({"data": [_shipping_dict(r) for r in rules], "message": "OK"})


@admin_bp.post("/shipping-rules")
@admin_required
def create_shipping_rule():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"data": None, "message": "name required"}), 400
    rule = ShippingRule(
        name=data["name"],
        min_order_amount=data.get("min_order_amount"),
        max_order_amount=data.get("max_order_amount"),
        flat_rate=data.get("flat_rate", 0.00),
        pincode_prefix=data.get("pincode_prefix"),
        is_active=data.get("is_active", True),
        priority=data.get("priority", 0),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify({"data": _shipping_dict(rule), "message": "Shipping rule created"}), 201


@admin_bp.put("/shipping-rules/<int:rule_id>")
@admin_required
def update_shipping_rule(rule_id):
    rule = ShippingRule.query.get_or_404(rule_id)
    data = request.get_json(silent=True) or {}
    for field in ("name", "min_order_amount", "max_order_amount", "flat_rate", "pincode_prefix", "is_active", "priority"):
        if field in data:
            setattr(rule, field, data[field])
    db.session.commit()
    return jsonify({"data": _shipping_dict(rule), "message": "Shipping rule updated"})


@admin_bp.delete("/shipping-rules/<int:rule_id>")
@admin_required
def delete_shipping_rule(rule_id):
    rule = ShippingRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"data": None, "message": "Shipping rule deleted"})
