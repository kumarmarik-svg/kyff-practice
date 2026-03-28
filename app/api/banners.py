from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.models import Banner

banners_bp = Blueprint("banners", __name__)


def _banner_dict(b):
    return {
        "id": b.id,
        "title": b.title,
        "subtitle": b.subtitle,
        "image_url": b.image_url,
        "link_url": b.link_url,
        "link_text": b.link_text,
        "position": b.position,
        "sort_order": b.sort_order,
        "starts_at": b.starts_at.isoformat() if b.starts_at else None,
        "ends_at": b.ends_at.isoformat() if b.ends_at else None,
    }


# GET /api/banners?position=home_hero
@banners_bp.get("/")
def list_banners():
    now = datetime.now(timezone.utc)
    position = request.args.get("position")

    q = Banner.query.filter(
        Banner.is_active == True,  # noqa: E712
        (Banner.starts_at == None) | (Banner.starts_at <= now),  # noqa: E711
        (Banner.ends_at == None) | (Banner.ends_at >= now),  # noqa: E711
    )
    if position:
        q = q.filter_by(position=position)

    banners = q.order_by(Banner.sort_order).all()
    return jsonify({"data": [_banner_dict(b) for b in banners], "message": "OK"})
