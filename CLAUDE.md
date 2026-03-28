# KYFF Store — Claude Code Context

## Project
D2C organic food ecommerce — Flask REST API backend + React SPA frontend.
See **[PLAN.md](./PLAN.md)** for the complete architecture, all 15 models, routes, backend build order, and full frontend plan.

## Stack

### Backend
- **Framework:** Flask 3 (app factory pattern, blueprints)
- **Database:** MySQL via SQLAlchemy + Flask-Migrate
- **Auth:** Flask-JWT-Extended (access 15 min + refresh 7 days)
- **Payments:** Razorpay (create order → verify HMAC-SHA256)
- **Validation:** Marshmallow schemas

### Frontend
- **Framework:** React 18 + Vite 5
- **Styling:** Tailwind CSS 3
- **Routing:** React Router v6
- **State:** Zustand (auth + cart) + TanStack Query (server state)
- **HTTP:** Axios with JWT refresh interceptor
- **Forms:** React Hook Form
- **Payments:** Razorpay.js (CDN)

## 15 Tables
`User` · `Address` · `PasswordResetToken` · `Category` · `Product` · `ProductVariant` · `ProductImage` · `Cart` · `CartItem` · `Order` · `OrderItem` · `Payment` · `Review` · `Banner` · `ShippingRule`

## Backend Conventions
- All responses: `{"data": ..., "message": "..."}` JSON envelope.
- Blueprints in `app/api/`, registered with `/api` prefix.
- Business logic in `app/services/`, never directly in route handlers.
- Models in `app/models/`, all imported in `app/models/__init__.py`.
- `@jwt_required` and `@admin_required` decorators in `app/utils/decorators.py`.
- `.env` is never committed — use `.env.example` as template.
- When `Product.has_variants=True`, stock/pricing live on `ProductVariant`, not `Product`.
- JWT identity stored as `str(user.id)`; always cast `int(get_jwt_identity())` in routes.

## Frontend Conventions
- All API calls go through `frontend/src/api/client.js` (Axios instance).
- `accessToken` stored in Zustand memory only (not localStorage) — XSS mitigation.
- `refreshToken` + `sessionKey` (guest cart UUID) stored in `localStorage`.
- Vite proxy: `/api/*` → `http://localhost:5000` in dev (no CORS issues).
- Guest cart uses `X-Session-Key` header; merged to user cart via `POST /api/cart/merge` on login.
- Admin pages sit under `/admin/*`, guarded by `AdminRoute` (checks `user.is_admin`).

## Key files

### Backend
| File | Purpose |
|---|---|
| `PLAN.md` | Full architecture — §1–5 backend, §6 frontend |
| `app/__init__.py` | App factory (`create_app`), accepts `test_config` dict |
| `app/extensions.py` | Shared instances: db, jwt, bcrypt |
| `app/config.py` | Dev / Prod / Test config classes, `_build_db_url` with `quote_plus` |
| `run.py` | Entry point |
| `seed.py` | Populates DB with sample data |

### Frontend (to be built)
| File | Purpose |
|---|---|
| `frontend/src/api/client.js` | Axios instance, JWT interceptor, refresh logic |
| `frontend/src/store/authStore.js` | Zustand: user, tokens, login/logout |
| `frontend/src/store/cartStore.js` | Zustand: sessionKey, itemCount |
| `frontend/src/App.jsx` | Route definitions, PrivateRoute, AdminRoute |

## Build order

### Backend (complete — Phases 1–9)
All 9 backend phases are done. 61/61 tests passing. DB seeded.

### Frontend — follow FE Phase 1 → 6 in PLAN.md §6
| Phase | What to build |
|---|---|
| FE-1 | Vite + Tailwind setup, Axios client, Navbar, Footer |
| FE-2 | Auth store, Login/Register pages, route guards |
| FE-3 | Home, Product list (paginated + filtered), Product detail |
| FE-4 | Cart drawer + page, qty stepper, guest→user merge |
| FE-5 | Checkout, Razorpay integration, Order confirm + history |
| FE-6 | Admin dashboard, Products/Orders/Users/Reviews/Banners/Shipping CRUD |
