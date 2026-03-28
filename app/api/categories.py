from flask import Blueprint, jsonify

from app.models import Category

categories_bp = Blueprint("categories", __name__)


def _category_dict(cat, include_children=False):
    d = {
        "id": cat.id,
        "name": cat.name,
        "slug": cat.slug,
        "description": cat.description,
        "image_url": cat.image_url,
        "parent_id": cat.parent_id,
        "is_active": cat.is_active,
        "sort_order": cat.sort_order,
    }
    if include_children:
        d["children"] = [_category_dict(c) for c in cat.children if c.is_active]
    return d


# GET /api/categories
@categories_bp.get("/")
def list_categories():
    # Return only top-level active categories with their active children
    categories = (
        Category.query
        .filter_by(is_active=True, parent_id=None)
        .order_by(Category.sort_order)
        .all()
    )
    return jsonify({
        "data": [_category_dict(c, include_children=True) for c in categories],
        "message": "OK",
    })


# GET /api/categories/<slug>
@categories_bp.get("/<slug>")
def get_category(slug):
    cat = Category.query.filter_by(slug=slug, is_active=True).first()
    if not cat:
        return jsonify({"data": None, "message": "Category not found"}), 404
    return jsonify({"data": _category_dict(cat, include_children=True), "message": "OK"})
