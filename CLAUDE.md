# KYFF Store — Claude Code Context

## Project
D2C organic food ecommerce — Flask REST API backend.
See **[PLAN.md](./PLAN.md)** for the complete architecture, all 15 models, routes, and build order.

## Stack
- **Framework:** Flask 3 (app factory pattern, blueprints)
- **Database:** MySQL via SQLAlchemy + Flask-Migrate
- **Auth:** Flask-JWT-Extended (access 15 min + refresh 7 days)
- **Payments:** Razorpay (create order → verify HMAC-SHA256)
- **Validation:** Marshmallow schemas

## 15 Tables
`User` · `Address` · `PasswordResetToken` · `Category` · `Product` · `ProductVariant` · `ProductImage` · `Cart` · `CartItem` · `Order` · `OrderItem` · `Payment` · `Review` · `Banner` · `ShippingRule`

## Conventions
- All responses: `{"data": ..., "message": "..."}` JSON envelope.
- Blueprints in `app/api/`, registered with `/api` prefix.
- Business logic in `app/services/`, never directly in route handlers.
- Models in `app/models/`, all imported in `app/models/__init__.py`.
- `@jwt_required` and `@admin_required` decorators in `app/utils/decorators.py`.
- `.env` is never committed — use `.env.example` as template.
- When `Product.has_variants=True`, stock/pricing live on `ProductVariant`, not `Product`.

## Key files
| File | Purpose |
|---|---|
| `PLAN.md` | Full architecture: 15 models, all routes, 9-phase build order |
| `app/__init__.py` | App factory (`create_app`) |
| `app/extensions.py` | Shared instances: db, jwt, bcrypt |
| `app/config.py` | Dev / Prod / Test config classes |
| `run.py` | Entry point |

## Build order
Follow **Phase 1 → 9** in PLAN.md §4. Do not skip phases. Models must all be created before any API work begins.
