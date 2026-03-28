"""
Seed script — populates kyff_practice_db with sample data.
Run with: flask shell < seed.py  OR  python seed.py
"""
from app import create_app
from app.extensions import bcrypt, db
from app.models import (
    Banner, Category, Product, ProductImage, ProductVariant, ShippingRule, User,
)

app = create_app("development")

with app.app_context():
    # -----------------------------------------------------------------------
    # Categories
    # -----------------------------------------------------------------------
    grains = Category(name="Grains & Cereals", slug="grains-cereals", sort_order=1,
                      description="Organic whole grains and cereals", is_active=True)
    pulses = Category(name="Pulses & Legumes", slug="pulses-legumes", sort_order=2,
                      description="High-protein organic pulses", is_active=True)
    oils = Category(name="Oils & Ghee", slug="oils-ghee", sort_order=3,
                    description="Cold-pressed organic oils and pure ghee", is_active=True)
    spices = Category(name="Spices & Herbs", slug="spices-herbs", sort_order=4,
                      description="Organic spices and herbs", is_active=True)
    db.session.add_all([grains, pulses, oils, spices])
    db.session.flush()

    # -----------------------------------------------------------------------
    # Products
    # -----------------------------------------------------------------------
    rice = Product(
        category_id=grains.id, name="Organic Basmati Rice", slug="organic-basmati-rice",
        sku="RICE-BAS-001", base_price=280.00, sale_price=249.00, stock_qty=200,
        short_description="Long-grain, aged organic basmati rice",
        description="Sourced directly from organic farms in the Himalayas. Naturally aged for superior aroma.",
        is_active=True, is_featured=True, is_organic_certified=True,
        tags="rice,basmati,grains,organic", weight_grams=1000,
    )
    wheat = Product(
        category_id=grains.id, name="Organic Whole Wheat", slug="organic-whole-wheat",
        sku="WHEAT-001", base_price=120.00, stock_qty=0, has_variants=True,
        short_description="Stone-ground whole wheat flour",
        is_active=True, is_organic_certified=True,
        tags="wheat,flour,grains,organic",
    )
    toor_dal = Product(
        category_id=pulses.id, name="Organic Toor Dal", slug="organic-toor-dal",
        sku="DAL-TOOR-001", base_price=180.00, sale_price=160.00, stock_qty=150,
        short_description="Premium split pigeon peas",
        is_active=True, is_featured=True, is_organic_certified=True,
        tags="dal,pulses,protein,organic", weight_grams=500,
    )
    coconut_oil = Product(
        category_id=oils.id, name="Cold-Pressed Coconut Oil", slug="cold-pressed-coconut-oil",
        sku="OIL-COC-001", base_price=450.00, stock_qty=80,
        short_description="100% pure cold-pressed virgin coconut oil",
        is_active=True, is_featured=True, is_organic_certified=True,
        tags="coconut,oil,cold-pressed,organic", weight_grams=500,
    )
    turmeric = Product(
        category_id=spices.id, name="Organic Turmeric Powder", slug="organic-turmeric-powder",
        sku="SPICE-TUR-001", base_price=95.00, stock_qty=300,
        short_description="High-curcumin organic turmeric",
        is_active=True, is_organic_certified=True,
        tags="turmeric,spices,haldi,organic", weight_grams=200,
    )
    db.session.add_all([rice, wheat, toor_dal, coconut_oil, turmeric])
    db.session.flush()

    # -----------------------------------------------------------------------
    # Variants (for wheat which has has_variants=True)
    # -----------------------------------------------------------------------
    db.session.add_all([
        ProductVariant(product_id=wheat.id, name="500g", sku="WHEAT-001-500G",
                       price=65.00, stock_qty=100, sort_order=1, is_active=True),
        ProductVariant(product_id=wheat.id, name="1kg", sku="WHEAT-001-1KG",
                       price=120.00, stock_qty=80, sort_order=2, is_active=True),
        ProductVariant(product_id=wheat.id, name="5kg", sku="WHEAT-001-5KG",
                       price=550.00, stock_qty=30, sort_order=3, is_active=True),
    ])

    # -----------------------------------------------------------------------
    # Product Images (placeholder URLs)
    # -----------------------------------------------------------------------
    db.session.add_all([
        ProductImage(product_id=rice.id, url="https://placehold.co/600x400?text=Basmati+Rice",
                     alt_text="Organic Basmati Rice", is_primary=True, sort_order=1),
        ProductImage(product_id=toor_dal.id, url="https://placehold.co/600x400?text=Toor+Dal",
                     alt_text="Organic Toor Dal", is_primary=True, sort_order=1),
        ProductImage(product_id=coconut_oil.id, url="https://placehold.co/600x400?text=Coconut+Oil",
                     alt_text="Cold-Pressed Coconut Oil", is_primary=True, sort_order=1),
    ])

    # -----------------------------------------------------------------------
    # Banners
    # -----------------------------------------------------------------------
    db.session.add_all([
        Banner(
            title="Fresh from the Farm", subtitle="100% Organic. 0% Compromise.",
            image_url="https://placehold.co/1200x400?text=KYFF+Hero",
            link_url="/products", link_text="Shop Now",
            position="home_hero", is_active=True, sort_order=1,
        ),
        Banner(
            title="Featured: Cold-Pressed Oils",
            image_url="https://placehold.co/1200x300?text=Oils+Sale",
            link_url="/products?category=oils-ghee", link_text="Explore Oils",
            position="home_mid", is_active=True, sort_order=1,
        ),
    ])

    # -----------------------------------------------------------------------
    # Shipping Rules
    # -----------------------------------------------------------------------
    db.session.add_all([
        ShippingRule(name="Free Shipping above ₹499", min_order_amount=499.00,
                     flat_rate=0.00, is_active=True, priority=10),
        ShippingRule(name="Standard Shipping", flat_rate=50.00,
                     is_active=True, priority=1),
    ])

    # -----------------------------------------------------------------------
    # Admin user
    # -----------------------------------------------------------------------
    admin = User(
        email="admin@kyff.store",
        password_hash=bcrypt.generate_password_hash("Admin@1234").decode(),
        first_name="KYFF", last_name="Admin",
        is_admin=True, is_active=True, email_verified=True,
    )
    db.session.add(admin)

    db.session.commit()
    print("Seed complete.")
    print("  Categories : 4")
    print("  Products   : 5 (1 with 3 variants)")
    print("  Banners    : 2")
    print("  Shipping   : 2 rules (free above ₹499, ₹50 standard)")
    print("  Admin user : admin@kyff.store / Admin@1234")
