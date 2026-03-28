import secrets
from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import bcrypt, db
from app.models import Address, PasswordResetToken, User


def register_user(data: dict) -> tuple[User, str, str]:
    if User.query.filter_by(email=data["email"].lower()).first():
        raise ValueError("Email already registered")

    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(
        email=data["email"].lower(),
        password_hash=password_hash,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone"),
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return user, access_token, refresh_token


def login_user(email: str, password: str) -> tuple[User, str, str]:
    user = User.query.filter_by(email=email.lower()).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise ValueError("Account is disabled")

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return user, access_token, refresh_token


def get_user_by_id(user_id: int) -> User:
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    return user


def update_user(user: User, data: dict) -> User:
    for field in ("first_name", "last_name", "phone"):
        if field in data:
            setattr(user, field, data[field])
    db.session.commit()
    return user


def create_password_reset_token(email: str) -> PasswordResetToken | None:
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return None  # Don't reveal whether email exists

    # Invalidate any existing unused tokens
    PasswordResetToken.query.filter_by(user_id=user.id, used_at=None).delete()

    token = PasswordResetToken(
        user_id=user.id,
        token=secrets.token_urlsafe(64),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.session.add(token)
    db.session.commit()
    return token


def reset_password(token_str: str, new_password: str) -> None:
    now = datetime.now(timezone.utc)
    record = PasswordResetToken.query.filter_by(token=token_str, used_at=None).first()

    if not record:
        raise ValueError("Invalid or already used token")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise ValueError("Token has expired")

    record.user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    record.used_at = now
    db.session.commit()


# --- Address helpers ---

def get_addresses(user: User) -> list[Address]:
    return Address.query.filter_by(user_id=user.id).all()


def create_address(user: User, data: dict) -> Address:
    if data.get("is_default"):
        Address.query.filter_by(user_id=user.id, is_default=True).update({"is_default": False})

    address = Address(
        user_id=user.id,
        label=data.get("label"),
        full_name=data["full_name"],
        phone=data["phone"],
        line1=data["line1"],
        line2=data.get("line2"),
        city=data["city"],
        state=data["state"],
        pincode=data["pincode"],
        is_default=data.get("is_default", False),
    )
    db.session.add(address)
    db.session.commit()
    return address


def update_address(user: User, address_id: int, data: dict) -> Address:
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        raise ValueError("Address not found")

    if data.get("is_default"):
        Address.query.filter_by(user_id=user.id, is_default=True).update({"is_default": False})

    for field in ("label", "full_name", "phone", "line1", "line2", "city", "state", "pincode", "is_default"):
        if field in data:
            setattr(address, field, data[field])
    db.session.commit()
    return address


def delete_address(user: User, address_id: int) -> None:
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        raise ValueError("Address not found")
    db.session.delete(address)
    db.session.commit()
