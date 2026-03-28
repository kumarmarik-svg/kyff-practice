# KYFF Store — D2C Organic Food Ecommerce

**Stack:** Flask · MySQL · SQLAlchemy · Razorpay · JWT
**Date:** 2026-03-27

---

## 1. Folder Structure

```
kyff-store/
├── app/
│   ├── __init__.py                  # App factory
│   ├── extensions.py                # db, jwt, bcrypt instances
│   ├── config.py                    # Config classes
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                  # User, Address, PasswordResetToken
│   │   ├── product.py               # Category, Product, ProductVariant, ProductImage
│   │   ├── cart.py                  # Cart, CartItem
│   │   ├── order.py                 # Order, OrderItem
│   │   ├── payment.py               # Payment
│   │   ├── review.py                # Review
│   │   ├── banner.py                # Banner
│   │   └── shipping.py              # ShippingRule
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py                  # /api/auth/*
│   │   ├── products.py              # /api/products/*
│   │   ├── categories.py            # /api/categories/*
│   │   ├── cart.py                  # /api/cart/*
│   │   ├── orders.py                # /api/orders/*
│   │   ├── payments.py              # /api/payments/*
│   │   ├── reviews.py               # /api/reviews/*
│   │   ├── banners.py               # /api/banners/*
│   │   └── admin.py                 # /api/admin/*
│   │
│   ├── services/
│   │   ├── auth_service.py          # Login, register, password reset
│   │   ├── cart_service.py          # Guest → user cart merge
│   │   ├── order_service.py         # Create order, stock deduction, shipping calc
│   │   ├── payment_service.py       # Razorpay create/verify
│   │   └── admin_service.py         # Dashboard stats
│   │
│   └── utils/
│       ├── decorators.py            # @admin_required, @jwt_required
│       ├── validators.py            # Marshmallow schemas
│       └── helpers.py               # Pagination, response formatters
│
├── migrations/                      # Flask-Migrate (Alembic)
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_cart.py
│   ├── test_orders.py
│   └── test_payments.py
│
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── admin/
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
│
├── .env                             # Never committed
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py                           # Entry point
└── PLAN.md
```

---

## 2. Models — All 15 Tables

### Relationship Map

```
User ──< Address
User ──< PasswordResetToken
User ──< Order
User ──< Review
User ──  Cart (one active cart)

Category ──< Category (self-ref parent/children)
Category ──< Product

Product ──< ProductVariant
Product ──< ProductImage
Product ──< CartItem
Product ──< OrderItem
Product ──< Review

ProductVariant ──< CartItem
ProductVariant ──< OrderItem

Cart ──< CartItem
Order ──< OrderItem
Order ──  Payment (one-to-one)

ShippingRule (standalone, applied at order creation)
Banner      (standalone, CMS content)
```

---

### 1. User (`users`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| email | VARCHAR(120) UNIQUE NOT NULL | |
| password_hash | VARCHAR(256) NOT NULL | bcrypt |
| first_name | VARCHAR(60) NOT NULL | |
| last_name | VARCHAR(60) NOT NULL | |
| phone | VARCHAR(15) | nullable |
| is_admin | BOOLEAN | default False |
| is_active | BOOLEAN | default True |
| email_verified | BOOLEAN | default False |
| created_at | DATETIME | server_default=now() |
| updated_at | DATETIME | onupdate=now() |

**Relationships:**
- `addresses` → many Address (backref `user`)
- `reset_tokens` → many PasswordResetToken (backref `user`)
- `cart` → one Cart (backref `user`)
- `orders` → many Order (backref `user`)
- `reviews` → many Review (backref `user`)

---

### 2. Address (`addresses`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| user_id | INT FK → users NOT NULL | CASCADE delete |
| label | VARCHAR(30) | "Home" / "Work" / "Other" |
| full_name | VARCHAR(120) NOT NULL | recipient name |
| phone | VARCHAR(15) NOT NULL | recipient phone |
| line1 | VARCHAR(200) NOT NULL | |
| line2 | VARCHAR(200) | nullable |
| city | VARCHAR(80) NOT NULL | |
| state | VARCHAR(80) NOT NULL | |
| pincode | VARCHAR(10) NOT NULL | |
| is_default | BOOLEAN | default False |

**Relationships:** → belongs to User

---

### 3. PasswordResetToken (`password_reset_tokens`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| user_id | INT FK → users NOT NULL | CASCADE delete |
| token | VARCHAR(128) UNIQUE NOT NULL | secrets.token_urlsafe(64) |
| expires_at | DATETIME NOT NULL | now() + 1 hour |
| used_at | DATETIME | nullable; set on use |
| created_at | DATETIME | server_default=now() |

**Relationships:** → belongs to User

---

### 4. Category (`categories`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(100) UNIQUE NOT NULL | |
| slug | VARCHAR(120) UNIQUE NOT NULL | URL-safe |
| description | TEXT | nullable |
| image_url | VARCHAR(500) | nullable |
| parent_id | INT FK → categories | nullable (self-referential) |
| is_active | BOOLEAN | default True |
| sort_order | INT | default 0 |

**Relationships:**
- `parent` → self (nullable)
- `children` → many self
- `products` → many Product

---

### 5. Product (`products`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| category_id | INT FK → categories NOT NULL | |
| name | VARCHAR(200) NOT NULL | |
| slug | VARCHAR(220) UNIQUE NOT NULL | |
| description | TEXT | |
| short_description | VARCHAR(500) | |
| base_price | DECIMAL(10,2) NOT NULL | MRP / base price |
| sale_price | DECIMAL(10,2) | nullable; overrides base_price |
| cost_price | DECIMAL(10,2) | nullable; admin-only |
| sku | VARCHAR(100) UNIQUE NOT NULL | |
| stock_qty | INT | default 0; used if no variants |
| low_stock_threshold | INT | default 5 |
| has_variants | BOOLEAN | default False |
| weight_grams | INT | nullable |
| is_active | BOOLEAN | default True |
| is_featured | BOOLEAN | default False |
| is_organic_certified | BOOLEAN | default False |
| tags | VARCHAR(500) | nullable; comma-separated |
| meta_title | VARCHAR(200) | nullable |
| meta_description | VARCHAR(500) | nullable |
| created_at | DATETIME | server_default=now() |
| updated_at | DATETIME | onupdate=now() |

**Relationships:**
- `category` → one Category
- `variants` → many ProductVariant (backref `product`)
- `images` → many ProductImage (backref `product`)
- `reviews` → many Review (backref `product`)

**Note:** When `has_variants=True`, stock and pricing are managed per-variant; `stock_qty` on product is ignored.

---

### 6. ProductVariant (`product_variants`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| product_id | INT FK → products NOT NULL | CASCADE delete |
| name | VARCHAR(100) NOT NULL | e.g. "500g", "1kg", "Pack of 3" |
| sku | VARCHAR(100) UNIQUE NOT NULL | |
| price | DECIMAL(10,2) NOT NULL | variant-specific price |
| sale_price | DECIMAL(10,2) | nullable |
| stock_qty | INT | default 0 |
| weight_grams | INT | nullable |
| is_active | BOOLEAN | default True |
| sort_order | INT | default 0 |

**Relationships:**
- `product` → one Product
- `cart_items` → many CartItem
- `order_items` → many OrderItem

---

### 7. ProductImage (`product_images`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| product_id | INT FK → products NOT NULL | CASCADE delete |
| url | VARCHAR(500) NOT NULL | |
| alt_text | VARCHAR(200) | nullable |
| sort_order | INT | default 0 |
| is_primary | BOOLEAN | default False |

**Relationships:** → belongs to Product

---

### 8. Cart (`carts`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| user_id | INT FK → users UNIQUE | nullable (guest); one cart per user |
| session_key | VARCHAR(128) UNIQUE | nullable; UUID for guest carts |
| created_at | DATETIME | server_default=now() |
| updated_at | DATETIME | onupdate=now() |

**Constraint:** exactly one of `user_id` or `session_key` must be set.

**Relationships:**
- `user` → one User (nullable)
- `items` → many CartItem (backref `cart`)

---

### 9. CartItem (`cart_items`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| cart_id | INT FK → carts NOT NULL | CASCADE delete |
| product_id | INT FK → products NOT NULL | |
| variant_id | INT FK → product_variants | nullable |
| quantity | INT NOT NULL | default 1, min 1 |
| unit_price | DECIMAL(10,2) NOT NULL | price snapshot at add time |

**UniqueConstraint:** (`cart_id`, `product_id`, `variant_id`) — prevents duplicate rows.

**Relationships:**
- `cart` → one Cart
- `product` → one Product
- `variant` → one ProductVariant (nullable)

---

### 10. Order (`orders`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| order_number | VARCHAR(20) UNIQUE NOT NULL | e.g. KYFF-20260001 |
| user_id | INT FK → users | nullable (guest checkout) |
| guest_email | VARCHAR(120) | nullable |
| guest_phone | VARCHAR(15) | nullable |
| status | ENUM NOT NULL | `pending` / `confirmed` / `processing` / `shipped` / `delivered` / `cancelled` / `refunded` |
| subtotal | DECIMAL(10,2) NOT NULL | sum of item totals |
| discount_amount | DECIMAL(10,2) | default 0.00 |
| shipping_amount | DECIMAL(10,2) | default 0.00 |
| tax_amount | DECIMAL(10,2) | default 0.00 |
| total_amount | DECIMAL(10,2) NOT NULL | final charged amount |
| shipping_address_snapshot | JSON NOT NULL | full address at order time |
| tracking_number | VARCHAR(100) | nullable; set when shipped |
| notes | TEXT | nullable; customer notes |
| created_at | DATETIME | server_default=now() |
| updated_at | DATETIME | onupdate=now() |

**Relationships:**
- `user` → one User (nullable)
- `items` → many OrderItem (backref `order`)
- `payment` → one Payment (backref `order`)

---

### 11. OrderItem (`order_items`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| order_id | INT FK → orders NOT NULL | CASCADE delete |
| product_id | INT FK → products | SET NULL on delete |
| variant_id | INT FK → product_variants | nullable; SET NULL on delete |
| product_name | VARCHAR(200) NOT NULL | snapshot |
| variant_name | VARCHAR(100) | nullable snapshot |
| product_sku | VARCHAR(100) NOT NULL | snapshot |
| quantity | INT NOT NULL | |
| unit_price | DECIMAL(10,2) NOT NULL | snapshot |
| total_price | DECIMAL(10,2) NOT NULL | quantity × unit_price |

**Relationships:**
- `order` → one Order
- `product` → one Product (nullable, kept for reference)
- `variant` → one ProductVariant (nullable)

---

### 12. Payment (`payments`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| order_id | INT FK → orders UNIQUE NOT NULL | one-to-one |
| razorpay_order_id | VARCHAR(100) UNIQUE NOT NULL | from Razorpay |
| razorpay_payment_id | VARCHAR(100) UNIQUE | nullable; set after capture |
| razorpay_signature | VARCHAR(256) | nullable; for HMAC verify |
| amount_paise | INT NOT NULL | total_amount × 100 |
| currency | VARCHAR(10) | default "INR" |
| status | ENUM NOT NULL | `created` / `paid` / `failed` / `refunded` |
| method | VARCHAR(50) | nullable; upi / card / netbanking / wallet |
| failure_reason | VARCHAR(300) | nullable |
| refund_id | VARCHAR(100) | nullable; Razorpay refund id |
| created_at | DATETIME | server_default=now() |
| updated_at | DATETIME | onupdate=now() |

**Relationships:** → one Order (unique FK)

---

### 13. Review (`reviews`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| product_id | INT FK → products NOT NULL | |
| user_id | INT FK → users NOT NULL | |
| order_item_id | INT FK → order_items | nullable; verify purchase |
| rating | TINYINT NOT NULL | 1–5 |
| title | VARCHAR(150) | nullable |
| body | TEXT | nullable |
| is_approved | BOOLEAN | default False; admin moderation |
| is_verified_purchase | BOOLEAN | default False |
| created_at | DATETIME | server_default=now() |
| updated_at | DATETIME | onupdate=now() |

**UniqueConstraint:** (`product_id`, `user_id`) — one review per product per user.

**Relationships:**
- `product` → one Product
- `user` → one User
- `order_item` → one OrderItem (nullable)

---

### 14. Banner (`banners`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| title | VARCHAR(200) NOT NULL | |
| subtitle | VARCHAR(300) | nullable |
| image_url | VARCHAR(500) NOT NULL | |
| link_url | VARCHAR(500) | nullable; CTA destination |
| link_text | VARCHAR(80) | nullable; CTA label |
| position | VARCHAR(50) | `home_hero` / `home_mid` / `category_top` |
| is_active | BOOLEAN | default True |
| sort_order | INT | default 0 |
| starts_at | DATETIME | nullable; scheduled activation |
| ends_at | DATETIME | nullable; scheduled expiry |

**Relationships:** none (standalone CMS record)

---

### 15. ShippingRule (`shipping_rules`)

| Field | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(100) NOT NULL | e.g. "Free Shipping", "Standard" |
| min_order_amount | DECIMAL(10,2) | nullable; threshold for free shipping |
| max_order_amount | DECIMAL(10,2) | nullable; upper bound |
| flat_rate | DECIMAL(10,2) | default 0.00; charged if rule matches |
| pincode_prefix | VARCHAR(10) | nullable; e.g. "400" matches Mumbai |
| is_active | BOOLEAN | default True |
| priority | INT | default 0; higher = evaluated first |

**Logic:** At order creation, `order_service` iterates active rules ordered by `priority DESC`, matches on `min_order_amount` / `pincode_prefix`, applies first matching rule's `flat_rate`.

**Relationships:** none (applied by service layer)

---

## 3. API Routes

```
# Auth
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
GET    /api/auth/me
PUT    /api/auth/me
POST   /api/auth/forgot-password
POST   /api/auth/reset-password

# Addresses
GET    /api/auth/addresses
POST   /api/auth/addresses
PUT    /api/auth/addresses/<id>
DELETE /api/auth/addresses/<id>

# Categories
GET    /api/categories
GET    /api/categories/<slug>

# Products
GET    /api/products
GET    /api/products/featured
GET    /api/products/search?q=
GET    /api/products/<slug>
GET    /api/products/<slug>/reviews

# Banners
GET    /api/banners?position=home_hero

# Cart
GET    /api/cart
POST   /api/cart/items
PUT    /api/cart/items/<id>
DELETE /api/cart/items/<id>
POST   /api/cart/merge

# Orders
POST   /api/orders
GET    /api/orders
GET    /api/orders/<order_number>

# Payments
POST   /api/payments/create
POST   /api/payments/verify

# Reviews
POST   /api/reviews
PUT    /api/reviews/<id>
DELETE /api/reviews/<id>

# Admin
GET    /api/admin/dashboard
GET    /api/admin/products
POST   /api/admin/products
PUT    /api/admin/products/<id>
DELETE /api/admin/products/<id>
GET    /api/admin/orders
PUT    /api/admin/orders/<id>/status
GET    /api/admin/users
PUT    /api/admin/users/<id>/toggle-active
GET    /api/admin/reviews
PUT    /api/admin/reviews/<id>/approve
GET    /api/admin/banners
POST   /api/admin/banners
PUT    /api/admin/banners/<id>
DELETE /api/admin/banners/<id>
GET    /api/admin/shipping-rules
POST   /api/admin/shipping-rules
PUT    /api/admin/shipping-rules/<id>
DELETE /api/admin/shipping-rules/<id>
```

---

## 4. Build Order

### Phase 1 — Foundation
1. `run.py` + `app/__init__.py` (app factory)
2. `app/extensions.py` (db, jwt, bcrypt)
3. `app/config.py` (Dev / Prod / Test)
4. `.env` from `.env.example`
5. Verify `flask run` returns 200

### Phase 2 — Models (all 15 tables)
6. `models/user.py` — User, Address, PasswordResetToken
7. `models/product.py` — Category, Product, ProductVariant, ProductImage
8. `models/cart.py` — Cart, CartItem
9. `models/order.py` — Order, OrderItem
10. `models/payment.py` — Payment
11. `models/review.py` — Review
12. `models/banner.py` — Banner
13. `models/shipping.py` — ShippingRule
14. `models/__init__.py` — import all models
15. `flask db init && flask db migrate && flask db upgrade`

### Phase 3 — Auth
16. `utils/decorators.py` (@jwt_required, @admin_required)
17. `services/auth_service.py` (hash, verify, tokens, reset flow)
18. `api/auth.py` (register, login, logout, refresh, me, addresses, forgot/reset password)

### Phase 4 — Catalog
19. `api/categories.py`
20. `api/products.py` (list, search, featured, detail, reviews)
21. `api/banners.py`

### Phase 5 — Cart
22. `services/cart_service.py` (add/update/remove, guest merge)
23. `api/cart.py`

### Phase 6 — Orders & Payments
24. `services/order_service.py` (stock deduction, order number gen, shipping rule calc)
25. `services/payment_service.py` (Razorpay create order + HMAC-SHA256 verify)
26. `api/orders.py`
27. `api/payments.py`

### Phase 7 — Reviews
28. `api/reviews.py` (create, edit, delete; verified purchase check)

### Phase 8 — Admin
29. `services/admin_service.py` (dashboard stats: revenue, orders, low stock)
30. `api/admin.py` (products, orders, users, reviews, banners, shipping rules)

### Phase 9 — Tests & Seed
31. `tests/conftest.py` + fixtures
32. Unit tests per module
33. Seed script: categories, products, variants, banners, shipping rules

---

## 5. Key Design Decisions

- **Guest cart** uses `session_key` (UUID, client-side); merges into user cart via `POST /api/cart/merge` on login.
- **Variants:** `has_variants=True` on Product delegates stock + pricing to `ProductVariant`. CartItem and OrderItem both carry optional `variant_id`.
- **Price snapshots** on CartItem (`unit_price`), OrderItem (`unit_price`, `product_name`, `variant_name`, `product_sku`), and `shipping_address_snapshot` on Order — prevents stale data if products change post-purchase.
- **Razorpay flow:** `POST /api/payments/create` → Razorpay order id → client Razorpay.js checkout → `POST /api/payments/verify` with HMAC-SHA256 signature → mark order confirmed + deduct stock.
- **Password reset:** `PasswordResetToken` with 1-hour TTL. Token is single-use (`used_at` set on redemption).
- **Reviews:** `is_verified_purchase` set automatically if `order_item_id` is provided and belongs to the user. `is_approved=False` by default — admin approves.
- **Shipping rules:** evaluated by priority at order creation; first match wins. Supports flat-rate, free-above-threshold, and pincode-restricted rules.
- **Banners:** `starts_at` / `ends_at` allow scheduled campaigns. Public API filters by `is_active=True AND (starts_at IS NULL OR starts_at <= now) AND (ends_at IS NULL OR ends_at >= now)`.
- **Soft deletes** not used; `is_active` flags keep FK integrity intact.
- **JWT:** 15-min access tokens + 7-day refresh tokens.

---

## 6. Frontend Plan — React + Vite + Tailwind CSS

### Overview

The frontend is a standalone SPA that lives in `frontend/` and talks exclusively to the Flask REST API at `/api/*`. It is built and served independently from the Flask app (Vite dev server in development, static build in production).

| Concern | Choice |
|---|---|
| Framework | React 18 |
| Build tool | Vite 5 |
| Styling | Tailwind CSS 3 |
| Routing | React Router v6 |
| State | Zustand (lightweight global store) |
| Data fetching | TanStack Query v5 (server state) |
| HTTP client | Axios (with interceptors for JWT refresh) |
| Forms | React Hook Form |
| Payments | Razorpay.js (loaded via CDN script tag) |
| Icons | Lucide React |

---

### Folder Structure

```
frontend/
├── index.html
├── vite.config.js           # proxy /api → Flask :5000
├── tailwind.config.js
├── postcss.config.js
├── package.json
│
└── src/
    ├── main.jsx             # ReactDOM.createRoot, QueryClientProvider, Router
    ├── App.jsx              # Route definitions
    │
    ├── api/                 # Axios instance + one file per resource
    │   ├── client.js        # baseURL, JWT interceptor, refresh logic
    │   ├── auth.js
    │   ├── products.js
    │   ├── categories.js
    │   ├── cart.js
    │   ├── orders.js
    │   ├── payments.js
    │   ├── reviews.js
    │   ├── banners.js
    │   └── admin.js
    │
    ├── store/               # Zustand slices
    │   ├── authStore.js     # user, accessToken, isLoggedIn, login(), logout()
    │   └── cartStore.js     # sessionKey (guest), itemCount, setItemCount()
    │
    ├── hooks/               # TanStack Query wrappers
    │   ├── useProducts.js
    │   ├── useCart.js
    │   ├── useOrders.js
    │   └── useAdmin.js
    │
    ├── components/
    │   ├── layout/
    │   │   ├── Navbar.jsx          # Logo, search, cart icon (count), auth links
    │   │   ├── Footer.jsx
    │   │   └── AdminLayout.jsx     # Sidebar + content area for admin pages
    │   │
    │   ├── ui/                     # Headless / reusable primitives
    │   │   ├── Button.jsx
    │   │   ├── Input.jsx
    │   │   ├── Modal.jsx
    │   │   ├── Toast.jsx           # Success / error notifications
    │   │   ├── Spinner.jsx
    │   │   ├── Pagination.jsx
    │   │   └── Badge.jsx           # "Organic", "Sale", stock status
    │   │
    │   ├── product/
    │   │   ├── ProductCard.jsx     # Image, name, price, add-to-cart button
    │   │   ├── ProductGrid.jsx     # Responsive grid of ProductCards
    │   │   ├── ProductFilters.jsx  # Category, organic, sort dropdowns
    │   │   ├── VariantSelector.jsx # Buttons for 500g / 1kg / 5kg etc.
    │   │   ├── ImageGallery.jsx    # Primary + thumbnail strip
    │   │   └── ReviewList.jsx      # Paginated approved reviews
    │   │
    │   ├── cart/
    │   │   ├── CartDrawer.jsx      # Slide-in panel (desktop)
    │   │   ├── CartItem.jsx        # Qty stepper, remove button
    │   │   └── CartSummary.jsx     # Subtotal, shipping estimate, checkout CTA
    │   │
    │   ├── checkout/
    │   │   ├── AddressForm.jsx     # Reusable address fields (React Hook Form)
    │   │   ├── AddressPicker.jsx   # Saved addresses + "use new address"
    │   │   └── RazorpayButton.jsx  # Loads Razorpay.js, opens checkout, calls verify
    │   │
    │   ├── auth/
    │   │   ├── LoginForm.jsx
    │   │   └── RegisterForm.jsx
    │   │
    │   └── admin/
    │       ├── StatsCard.jsx         # Revenue / orders / users / low-stock tiles
    │       ├── DataTable.jsx         # Generic sortable table with pagination
    │       ├── ProductForm.jsx       # Create / edit product (with variants)
    │       ├── OrderStatusSelect.jsx # Dropdown for status + tracking number
    │       ├── BannerForm.jsx
    │       └── ShippingRuleForm.jsx
    │
    └── pages/
        ├── HomePage.jsx
        ├── ProductListPage.jsx
        ├── ProductDetailPage.jsx
        ├── CartPage.jsx
        ├── CheckoutPage.jsx
        ├── OrderConfirmPage.jsx
        ├── OrderHistoryPage.jsx
        ├── OrderDetailPage.jsx
        ├── LoginPage.jsx
        ├── RegisterPage.jsx
        ├── ProfilePage.jsx
        └── admin/
            ├── AdminDashboardPage.jsx
            ├── AdminProductsPage.jsx
            ├── AdminOrdersPage.jsx
            ├── AdminUsersPage.jsx
            ├── AdminReviewsPage.jsx
            ├── AdminBannersPage.jsx
            └── AdminShippingPage.jsx
```

---

### State Management

#### Zustand — `authStore`
```
{ user, accessToken, refreshToken, isLoggedIn }
Actions: login(tokens, user), logout(), setAccessToken(token)
Persisted to: localStorage (refreshToken only — access token in memory)
```

#### Zustand — `cartStore`
```
{ sessionKey, itemCount }
Actions: initSessionKey(), setItemCount(n), clearCart()
sessionKey: UUID generated on first visit, stored in localStorage
itemCount: kept in sync after every cart mutation for Navbar badge
```

#### TanStack Query — server state
All API data (products, cart contents, orders, admin tables) lives in TanStack Query cache. Zustand only holds auth tokens and the guest session key.

---

### API Integration

#### `src/api/client.js`
```
- baseURL: /api  (Vite proxy → Flask :5000 in dev)
- Request interceptor: attach Authorization: Bearer <accessToken> from authStore
- Response interceptor (401): call POST /api/auth/refresh → update accessToken → retry original request
- Guest cart header: attach X-Session-Key from cartStore.sessionKey on all cart requests
```

#### Resource modules (examples)
```
auth.js      → register, login, logout, me, updateMe, forgotPassword, resetPassword, addresses CRUD
products.js  → list(params), featured(), search(q), detail(slug), reviews(slug, page)
cart.js      → get, addItem, updateItem, removeItem, merge(sessionKey)
orders.js    → create(payload), list(), get(orderNumber)
payments.js  → create(orderNumber), verify(payload)
admin.js     → dashboard, products CRUD, orders list+status, users list+toggle, reviews+approve, banners CRUD, shipping CRUD
```

---

### Page Breakdown

#### FE-1 — Home (`HomePage`)
- Fetch: `GET /api/banners?position=home_hero`, `GET /api/categories`, `GET /api/products?featured=true`
- Components: `<HeroBanner>` (auto-slide), `<CategoryStrip>`, `<ProductGrid limit=8>`
- On mount: init `cartStore.sessionKey` if not set

#### FE-2 — Product List (`ProductListPage`)
- Route: `/products?category=<slug>&q=<search>&page=<n>`
- Fetch: `GET /api/products` with query params
- Components: `<ProductFilters>`, `<ProductGrid>`, `<Pagination>`
- URL-driven filters — React Router `useSearchParams`

#### FE-3 — Product Detail (`ProductDetailPage`)
- Route: `/products/:slug`
- Fetch: `GET /api/products/:slug`, `GET /api/products/:slug/reviews`
- Components: `<ImageGallery>`, `<VariantSelector>`, qty input, `<AddToCartButton>`, `<ReviewList>`
- Variant selection updates displayed price; `variant_id` sent to cart API

#### FE-4 — Cart (`CartPage` + `CartDrawer`)
- Fetch: `GET /api/cart` (header: `X-Session-Key` or JWT)
- Components: `<CartItem>` (qty stepper → `PUT /api/cart/items/:id`), `<CartSummary>`
- On login: `POST /api/cart/merge` → invalidate cart query → update `cartStore.itemCount`

#### FE-5 — Checkout (`CheckoutPage`)
- Protected route (redirect to login if not authenticated)
- Steps: address selection → order summary → pay
- `POST /api/orders` → get `order_number`
- `POST /api/payments/create` → get `razorpay_order_id`
- Open Razorpay.js modal → on success: `POST /api/payments/verify` → redirect to `OrderConfirmPage`

#### FE-6 — Auth (`LoginPage` / `RegisterPage`)
- `LoginPage`: calls `POST /api/auth/login` → stores tokens in authStore → triggers cart merge → redirect
- `RegisterPage`: calls `POST /api/auth/register` → same flow
- Redirect back to previous page using React Router `state.from`

#### FE-7 — Admin (`/admin/*`)
- Protected by `isAdmin` check in route guard (`AdminRoute` wrapper)
- `AdminDashboardPage`: stats tiles from `GET /api/admin/dashboard`
- `AdminProductsPage`: paginated `<DataTable>` + `<ProductForm>` modal for create/edit
- `AdminOrdersPage`: filterable by status, inline `<OrderStatusSelect>`
- `AdminUsersPage`: paginated table, toggle-active button
- `AdminReviewsPage`: filter by `approved=false`, approve button
- `AdminBannersPage`: `<BannerForm>` modal, sort_order drag-handle (future)
- `AdminShippingPage`: `<ShippingRuleForm>` modal

---

### Frontend Build Order

#### FE Phase 1 — Setup
1. `npm create vite@latest frontend -- --template react`
2. Install: `tailwindcss`, `react-router-dom`, `zustand`, `@tanstack/react-query`, `axios`, `react-hook-form`, `lucide-react`
3. Configure Vite proxy: `/api` → `http://localhost:5000`
4. Set up Tailwind, base layout (`Navbar`, `Footer`)
5. Create `api/client.js` with JWT interceptor

#### FE Phase 2 — Auth + Store
6. `authStore.js` + `cartStore.js` (Zustand, localStorage persistence)
7. `LoginPage` + `RegisterPage` — connect to `/api/auth`
8. Protected route wrapper (`PrivateRoute`, `AdminRoute`)
9. `Navbar` shows user name / logout when logged in

#### FE Phase 3 — Catalog
10. `HomePage` — banners, categories, featured products
11. `ProductListPage` — paginated grid with filters and search
12. `ProductDetailPage` — gallery, variants, add to cart

#### FE Phase 4 — Cart
13. `cartStore` itemCount badge in `Navbar`
14. `CartDrawer` (slide-in) + `CartPage` (full page)
15. Qty stepper, remove item, subtotal
16. Cart merge on login

#### FE Phase 5 — Checkout & Orders
17. `CheckoutPage` — address picker + `AddressForm`
18. `RazorpayButton` — full Razorpay.js integration
19. `OrderConfirmPage`, `OrderHistoryPage`, `OrderDetailPage`

#### FE Phase 6 — Admin
20. `AdminLayout` — sidebar with nav links
21. `AdminDashboardPage` — stats tiles
22. `AdminProductsPage` — CRUD with `ProductForm` modal (variants support)
23. `AdminOrdersPage` — status update inline
24. `AdminUsersPage`, `AdminReviewsPage`, `AdminBannersPage`, `AdminShippingPage`

---

### Key Frontend Design Decisions

- **No SSR** — pure SPA. SEO handled via meta tags for now; can add React Helmet later.
- **Guest cart persistence** — `sessionKey` UUID in `localStorage`. On login, `POST /api/cart/merge` unifies carts.
- **JWT in memory** — `accessToken` in Zustand (not localStorage) to reduce XSS risk. `refreshToken` in localStorage with 7-day TTL.
- **Axios 401 interceptor** — transparently refreshes the access token and retries the original request. User never sees a flash of "logged out".
- **Vite proxy** — all `/api/*` requests proxied to Flask in dev, so no CORS issues during development. In production, Nginx serves both the React build and proxies `/api` to Gunicorn.
- **TanStack Query** — `queryKey` conventions: `['products', params]`, `['cart']`, `['orders']`, `['admin', 'products', page]`. Mutations invalidate relevant queries on success.
- **Razorpay flow** — `RazorpayButton` dynamically loads `https://checkout.razorpay.com/v1/checkout.js`, opens the modal with `razorpay_order_id` from our API, and on `payment.success` calls `POST /api/payments/verify`. On failure, shows a Toast and allows retry without recreating the order.
- **Tailwind design tokens** — extend `tailwind.config.js` with KYFF brand colours (earthy greens and warm neutrals) so all components use consistent design tokens.
