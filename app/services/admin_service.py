from sqlalchemy import func

from app.extensions import db
from app.models import Order, Product, Review, User
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus


def get_dashboard_stats() -> dict:
    total_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(Order.status.in_([
        OrderStatus.confirmed, OrderStatus.processing,
        OrderStatus.shipped, OrderStatus.delivered,
    ])).scalar()

    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status=OrderStatus.pending).count()

    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    total_products = Product.query.count()
    low_stock = Product.query.filter(
        Product.has_variants == False,  # noqa: E712
        Product.stock_qty <= Product.low_stock_threshold,
        Product.is_active == True,  # noqa: E712
    ).count()

    pending_reviews = Review.query.filter_by(is_approved=False).count()

    return {
        "revenue": {
            "total": str(total_revenue),
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
        },
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "products": {
            "total": total_products,
            "low_stock": low_stock,
        },
        "reviews": {
            "pending_approval": pending_reviews,
        },
    }
