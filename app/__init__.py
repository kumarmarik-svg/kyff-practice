import os
from flask import Flask
from .extensions import db, migrate, jwt, bcrypt
from .config import config_map


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    from .api.auth import auth_bp
    from .api.categories import categories_bp
    from .api.products import products_bp
    from .api.banners import banners_bp
    from .api.cart import cart_bp
    from .api.orders import orders_bp
    from .api.payments import payments_bp
    from .api.reviews import reviews_bp
    from .api.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(banners_bp, url_prefix="/api/banners")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(reviews_bp, url_prefix="/api/reviews")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        return {"data": None, "message": "OK"}

    return app
