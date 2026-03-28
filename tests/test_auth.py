from tests.conftest import auth


class TestRegister:
    def test_success(self, client):
        res = client.post("/api/auth/register", json={
            "email": "new@example.com", "password": "pass1234",
            "first_name": "New", "last_name": "User",
        })
        assert res.status_code == 201
        data = res.get_json()["data"]
        assert data["user"]["email"] == "new@example.com"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_duplicate_email(self, client, user):
        res = client.post("/api/auth/register", json={
            "email": user.email, "password": "pass1234",
            "first_name": "X", "last_name": "Y",
        })
        assert res.status_code == 409

    def test_missing_fields(self, client):
        res = client.post("/api/auth/register", json={"email": "x@x.com"})
        assert res.status_code == 400


class TestLogin:
    def test_success(self, client, user):
        res = client.post("/api/auth/login", json={"email": user.email, "password": "password123"})
        assert res.status_code == 200
        assert "access_token" in res.get_json()["data"]

    def test_wrong_password(self, client, user):
        res = client.post("/api/auth/login", json={"email": user.email, "password": "wrong"})
        assert res.status_code == 401

    def test_unknown_email(self, client):
        res = client.post("/api/auth/login", json={"email": "nobody@x.com", "password": "x"})
        assert res.status_code == 401


class TestMe:
    def test_get_me(self, client, user, user_token):
        res = client.get("/api/auth/me", headers=auth(user_token))
        assert res.status_code == 200
        assert res.get_json()["data"]["email"] == user.email

    def test_requires_auth(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_update_me(self, client, user_token):
        res = client.put("/api/auth/me", json={"first_name": "Updated"}, headers=auth(user_token))
        assert res.status_code == 200
        assert res.get_json()["data"]["first_name"] == "Updated"


class TestAddresses:
    ADDR = {
        "full_name": "Test User", "phone": "9999999999",
        "line1": "123 Street", "city": "Mumbai",
        "state": "Maharashtra", "pincode": "400001",
    }

    def test_create_and_list(self, client, user_token):
        res = client.post("/api/auth/addresses", json=self.ADDR, headers=auth(user_token))
        assert res.status_code == 201
        res = client.get("/api/auth/addresses", headers=auth(user_token))
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 1

    def test_update(self, client, user_token):
        create_res = client.post("/api/auth/addresses", json=self.ADDR, headers=auth(user_token))
        addr_id = create_res.get_json()["data"]["id"]
        res = client.put(f"/api/auth/addresses/{addr_id}", json={"city": "Delhi"}, headers=auth(user_token))
        assert res.status_code == 200
        assert res.get_json()["data"]["city"] == "Delhi"

    def test_delete(self, client, user_token):
        create_res = client.post("/api/auth/addresses", json=self.ADDR, headers=auth(user_token))
        addr_id = create_res.get_json()["data"]["id"]
        res = client.delete(f"/api/auth/addresses/{addr_id}", headers=auth(user_token))
        assert res.status_code == 200
        assert len(client.get("/api/auth/addresses", headers=auth(user_token)).get_json()["data"]) == 0

    def test_missing_fields(self, client, user_token):
        res = client.post("/api/auth/addresses", json={"full_name": "X"}, headers=auth(user_token))
        assert res.status_code == 400


class TestPasswordReset:
    def test_forgot_password_returns_token(self, client, user):
        res = client.post("/api/auth/forgot-password", json={"email": user.email})
        assert res.status_code == 200
        assert res.get_json()["data"]["reset_token"] is not None

    def test_forgot_unknown_email_returns_null_token(self, client):
        res = client.post("/api/auth/forgot-password", json={"email": "nobody@x.com"})
        assert res.status_code == 200
        assert res.get_json()["data"]["reset_token"] is None

    def test_reset_password(self, client, user):
        token_res = client.post("/api/auth/forgot-password", json={"email": user.email})
        token = token_res.get_json()["data"]["reset_token"]
        res = client.post("/api/auth/reset-password", json={"token": token, "password": "newpass123"})
        assert res.status_code == 200
        # Can now login with new password
        login_res = client.post("/api/auth/login", json={"email": user.email, "password": "newpass123"})
        assert login_res.status_code == 200

    def test_reset_invalid_token(self, client):
        res = client.post("/api/auth/reset-password", json={"token": "badtoken", "password": "x"})
        assert res.status_code == 400
