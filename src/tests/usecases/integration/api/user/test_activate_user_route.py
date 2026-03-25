from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestActivateUserRoute:
    def test_activate_user_route_success(self, client: TestClient, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=hasher.hash(raw_code),
            activation_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            roles={"cliente"},
        )
        repository.add_user(user=user)

        response = client.post(
            "/users/activate/",
            json={
                "email": "john@example.com",
                "activation_code": raw_code,
            },
        )

        assert response.status_code == 200

        body = response.json()
        assert "json" in body
        assert body["json"]["id"] == str(user.id)
        assert body["json"]["name"] == "John Doe"
        assert body["json"]["email"] == "john@example.com"
        assert body["json"]["is_active"] is True
        assert body["json"]["roles"] == ["cliente"]

        updated_user = repository.find_user_by_id(user_id=user.id)
        assert updated_user.is_active is True
        assert updated_user.activation_code is None
        assert updated_user.activation_code_expires_at is None

    def test_activate_user_route_returns_error_when_code_is_invalid(
        self, client: TestClient, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=hasher.hash("abc12345"),
            activation_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            roles={"cliente"},
        )
        repository.add_user(user=user)

        response = client.post(
            "/users/activate/",
            json={
                "email": "john@example.com",
                "activation_code": "wrong-code",
            },
        )

        assert response.status_code == 401
        body = response.json()
        assert "detail" in body
        assert "invalid" in body["detail"].lower()

        persisted_user = repository.find_user_by_id(user_id=user.id)
        assert persisted_user.is_active is False
        assert persisted_user.activation_code is not None
        assert persisted_user.activation_code_expires_at is not None