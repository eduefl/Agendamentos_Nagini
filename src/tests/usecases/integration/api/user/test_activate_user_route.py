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

    def test_activate_user_route_success_provider(self, client: TestClient, tst_db_session, make_user, seed_roles):
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
            roles={"prestador"},
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
        assert body["json"]["roles"] == ["prestador"]

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

        assert response.status_code == 400
        body = response.json()
        assert "detail" in body
        assert "invalid" in body["detail"].lower()

        persisted_user = repository.find_user_by_id(user_id=user.id)
        assert persisted_user.is_active is False
        assert persisted_user.activation_code is not None
        assert persisted_user.activation_code_expires_at is not None

    def test_activate_user_when_user_already_active_route(self, client: TestClient, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=True,
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

        assert response.status_code == 409
        body = response.json()
        assert "detail" in body
        assert "already active" in body["detail"].lower()
        assert "user with email" in body["detail"].lower()
        



    def test_activate_user_when_activation_code_is_none_route(self, client: TestClient, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
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

        assert response.status_code == 400
        body = response.json()
        assert "detail" in body
        assert "invalid activation code" in body["detail"].lower()
        
    def test_activate_user_when_activation_code_is_expired(self, client: TestClient, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"
        user = make_user(
            name="Jane Doe",
            email="jane@example.com",
            is_active=False,
            activation_code=hasher.hash(raw_code),
            activation_code_expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Set to expired
            roles={"cliente"},
        )
        repository.add_user(user=user)

        response = client.post(
            "/users/activate/",
            json={
                "email": "jane@example.com",
                "activation_code": raw_code,
            },
        )

        assert response.status_code == 410
        body = response.json()
        assert "detail" in body
        assert "activation code has expired" in body["detail"].lower()

    def test_activate_user_when_email_is_not_found_route(self, client: TestClient, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"
        user = make_user(
            name="Jane Doe",
            email="jane@example.com",
            is_active=False,
            activation_code=hasher.hash(raw_code),
            activation_code_expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Set to expired
            roles={"cliente"},
        )
        repository.add_user(user=user)

        response = client.post(
            "/users/activate/",
            json={
                "email": "jon@example.com",
                "activation_code": raw_code,
            },
        )

        assert response.status_code == 404
        body = response.json()
        assert "detail" in body
        assert "user with" in body["detail"].lower()
        assert "email" in body["detail"].lower()
        assert "not found" in body["detail"].lower()
