import pytest

from app import create_app
from app.extensions import db as _db
from app.models import (
    Banner, Cart, Category, Order, Payment, Product,
    ProductVariant, ShippingRule, User,
)
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus


@pytest.fixture(scope="session")
def app():
    app = create_app("testing", test_config={
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "JWT_SECRET_KEY": "test-secret-key-that-is-long-enough-for-hs256",
        "RAZORPAY_KEY_ID": "rzp_test_key",
        "RAZORPAY_KEY_SECRET": "test_secret",
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Truncate all tables between tests
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture(scope="function")
def client(app, db):
    return app.test_client()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    from app.extensions import bcrypt
    u = User(
        email="test@example.com",
        password_hash=bcrypt.generate_password_hash("password123").decode(),
        first_name="Test", last_name="User",
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin_user(db):
    from app.extensions import bcrypt
    u = User(
        email="admin@example.com",
        password_hash=bcrypt.generate_password_hash("adminpass").decode(),
        first_name="Admin", last_name="User", is_admin=True,
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def user_token(client, user):
    res = client.post("/api/auth/login", json={"email": user.email, "password": "password123"})
    return res.get_json()["data"]["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    res = client.post("/api/auth/login", json={"email": admin_user.email, "password": "adminpass"})
    return res.get_json()["data"]["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Catalog fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def category(db):
    cat = Category(name="Grains", slug="grains", is_active=True)
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def product(db, category):
    p = Product(
        category_id=category.id, name="Organic Rice", slug="organic-rice",
        sku="RICE-001", base_price=120.00, stock_qty=50,
        is_active=True, is_featured=True,
    )
    db.session.add(p)
    db.session.commit()
    return p


@pytest.fixture
def product_with_variant(db, category):
    p = Product(
        category_id=category.id, name="Organic Wheat", slug="organic-wheat",
        sku="WHEAT-001", base_price=100.00, has_variants=True, is_active=True,
    )
    db.session.add(p)
    db.session.flush()
    v = ProductVariant(
        product_id=p.id, name="1kg", sku="WHEAT-001-1KG",
        price=110.00, stock_qty=30, is_active=True,
    )
    db.session.add(v)
    db.session.commit()
    return p, v


@pytest.fixture
def shipping_rule(db):
    rule = ShippingRule(name="Standard", flat_rate=50.00, is_active=True, priority=1)
    db.session.add(rule)
    db.session.commit()
    return rule


SHIPPING_ADDR = {
    "full_name": "Test User", "phone": "9999999999",
    "line1": "123 Main St", "city": "Mumbai",
    "state": "Maharashtra", "pincode": "400001",
}
