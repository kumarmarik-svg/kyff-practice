from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.models import Product, Review

products_bp = Blueprint("products", __name__)


def _variant_dict(v):
    return {
        "id": v.id,
        "name": v.name,
        "sku": v.sku,
        "price": str(v.price),
        "sale_price": str(v.sale_price) if v.sale_price else None,
        "stock_qty": v.stock_qty,
        "weight_grams": v.weight_grams,
        "is_active": v.is_active,
        "sort_order": v.sort_order,
    }


def _image_dict(img):
    return {
        "id": img.id,
        "url": img.url,
        "alt_text": img.alt_text,
        "sort_order": img.sort_order,
        "is_primary": img.is_primary,
    }


def _product_dict(p, detail=False):
    d = {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "short_description": p.short_description,
        "base_price": str(p.base_price),
        "sale_price": str(p.sale_price) if p.sale_price else None,
        "sku": p.sku,
        "has_variants": p.has_variants,
        "stock_qty": p.stock_qty if not p.has_variants else None,
        "is_organic_certified": p.is_organic_certified,
        "is_featured": p.is_featured,
        "tags": p.tags,
        "category_id": p.category_id,
        "primary_image": next(
            (_image_dict(img) for img in p.images if img.is_primary),
            _image_dict(p.images[0]) if p.images else None,
        ),
    }
    if detail:
        d.update({
            "description": p.description,
            "cost_price": None,  # never expose to public
            "weight_grams": p.weight_grams,
            "low_stock_threshold": None,  # admin-only
            "meta_title": p.meta_title,
            "meta_description": p.meta_description,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "variants": [_variant_dict(v) for v in p.variants if v.is_active],
            "images": [_image_dict(img) for img in sorted(p.images, key=lambda i: i.sort_order)],
        })
    return d


def _review_dict(r):
    return {
        "id": r.id,
        "user_id": r.user_id,
        "rating": r.rating,
        "title": r.title,
        "body": r.body,
        "is_verified_purchase": r.is_verified_purchase,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _active_products_query():
    return Product.query.filter_by(is_active=True)


# GET /api/products
@products_bp.get("/")
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    category = request.args.get("category")
    organic = request.args.get("organic")

    q = _active_products_query()
    if category:
        from app.models import Category
        cat = Category.query.filter_by(slug=category, is_active=True).first()
        if cat:
            q = q.filter_by(category_id=cat.id)
    if organic:
        q = q.filter_by(is_organic_certified=True)

    pagination = q.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "data": {
            "items": [_product_dict(p) for p in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        },
        "message": "OK",
    })


# GET /api/products/featured
@products_bp.get("/featured")
def featured_products():
    products = _active_products_query().filter_by(is_featured=True).order_by(Product.id.desc()).limit(20).all()
    return jsonify({"data": [_product_dict(p) for p in products], "message": "OK"})


# GET /api/products/search?q=
@products_bp.get("/search")
def search_products():
    q_term = request.args.get("q", "").strip()
    if not q_term:
        return jsonify({"data": [], "message": "Query required"}), 400

    like = f"%{q_term}%"
    products = (
        _active_products_query()
        .filter(
            Product.name.ilike(like)
            | Product.tags.ilike(like)
            | Product.short_description.ilike(like)
        )
        .limit(50)
        .all()
    )
    return jsonify({"data": [_product_dict(p) for p in products], "message": "OK"})


# GET /api/products/<slug>
@products_bp.get("/<slug>")
def get_product(slug):
    p = _active_products_query().filter_by(slug=slug).first()
    if not p:
        return jsonify({"data": None, "message": "Product not found"}), 404
    return jsonify({"data": _product_dict(p, detail=True), "message": "OK"})


# GET /api/products/<slug>/reviews
@products_bp.get("/<slug>/reviews")
def get_product_reviews(slug):
    p = _active_products_query().filter_by(slug=slug).first()
    if not p:
        return jsonify({"data": None, "message": "Product not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)

    pagination = (
        Review.query
        .filter_by(product_id=p.id, is_approved=True)
        .order_by(Review.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "data": {
            "items": [_review_dict(r) for r in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        },
        "message": "OK",
    })
