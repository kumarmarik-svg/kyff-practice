from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity

from app.services import auth_service
from app.utils.decorators import jwt_required

auth_bp = Blueprint("auth", __name__)


def _user_dict(user):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _address_dict(addr):
    return {
        "id": addr.id,
        "label": addr.label,
        "full_name": addr.full_name,
        "phone": addr.phone,
        "line1": addr.line1,
        "line2": addr.line2,
        "city": addr.city,
        "state": addr.state,
        "pincode": addr.pincode,
        "is_default": addr.is_default,
    }


# POST /api/auth/register
@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ("email", "password", "first_name", "last_name")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"data": None, "message": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        user, access_token, refresh_token = auth_service.register_user(data)
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 409

    return jsonify({
        "data": {"user": _user_dict(user), "access_token": access_token, "refresh_token": refresh_token},
        "message": "Registration successful",
    }), 201


# POST /api/auth/login
@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    if not data.get("email") or not data.get("password"):
        return jsonify({"data": None, "message": "Email and password required"}), 400

    try:
        user, access_token, refresh_token = auth_service.login_user(data["email"], data["password"])
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 401

    return jsonify({
        "data": {"user": _user_dict(user), "access_token": access_token, "refresh_token": refresh_token},
        "message": "Login successful",
    })


# POST /api/auth/logout
@auth_bp.post("/logout")
@jwt_required
def logout():
    # JWT is stateless; client discards tokens. Server-side blocklist can be added later.
    return jsonify({"data": None, "message": "Logged out successfully"})


# POST /api/auth/refresh
@auth_bp.post("/refresh")
@jwt_required
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"data": {"access_token": access_token}, "message": "Token refreshed"})


# GET /api/auth/me
@auth_bp.get("/me")
@jwt_required
def me():
    user = auth_service.get_user_by_id(int(get_jwt_identity()))
    return jsonify({"data": _user_dict(user), "message": "OK"})


# PUT /api/auth/me
@auth_bp.put("/me")
@jwt_required
def update_me():
    user = auth_service.get_user_by_id(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    user = auth_service.update_user(user, data)
    return jsonify({"data": _user_dict(user), "message": "Profile updated"})


# POST /api/auth/forgot-password
@auth_bp.post("/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    if not data.get("email"):
        return jsonify({"data": None, "message": "Email required"}), 400

    token_record = auth_service.create_password_reset_token(data["email"])
    # In production: send token_record.token via email. Here we expose it for dev/testing.
    token_val = token_record.token if token_record else None
    return jsonify({
        "data": {"reset_token": token_val},
        "message": "If that email exists, a reset token has been generated",
    })


# POST /api/auth/reset-password
@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    if not data.get("token") or not data.get("password"):
        return jsonify({"data": None, "message": "Token and new password required"}), 400

    try:
        auth_service.reset_password(data["token"], data["password"])
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 400

    return jsonify({"data": None, "message": "Password reset successful"})


# --- Addresses ---

# GET /api/auth/addresses
@auth_bp.get("/addresses")
@jwt_required
def list_addresses():
    user = auth_service.get_user_by_id(int(get_jwt_identity()))
    return jsonify({"data": [_address_dict(a) for a in auth_service.get_addresses(user)], "message": "OK"})


# POST /api/auth/addresses
@auth_bp.post("/addresses")
@jwt_required
def create_address():
    user = auth_service.get_user_by_id(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    required = ("full_name", "phone", "line1", "city", "state", "pincode")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"data": None, "message": f"Missing fields: {', '.join(missing)}"}), 400

    address = auth_service.create_address(user, data)
    return jsonify({"data": _address_dict(address), "message": "Address created"}), 201


# PUT /api/auth/addresses/<id>
@auth_bp.put("/addresses/<int:address_id>")
@jwt_required
def update_address(address_id):
    user = auth_service.get_user_by_id(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    try:
        address = auth_service.update_address(user, address_id, data)
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 404
    return jsonify({"data": _address_dict(address), "message": "Address updated"})


# DELETE /api/auth/addresses/<id>
@auth_bp.delete("/addresses/<int:address_id>")
@jwt_required
def delete_address(address_id):
    user = auth_service.get_user_by_id(int(get_jwt_identity()))
    try:
        auth_service.delete_address(user, address_id)
    except ValueError as e:
        return jsonify({"data": None, "message": str(e)}), 404
    return jsonify({"data": None, "message": "Address deleted"})
