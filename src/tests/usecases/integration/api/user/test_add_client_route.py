from datetime import datetime, timedelta, timezone
import uuid

from fastapi.testclient import TestClient

from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestAddClientRoute:
    def test_add_client_route_success(self, client: TestClient, tst_db_session, make_user, seed_roles):
        response = client.post("/users/clients/", json={
			"name": "John Doe",
			"email": "john.doe@example.com",
			"password": "securepassword"
		})
        assert response.status_code == 201
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        assert "json" in body
        assert uuid.UUID(body["json"]["id"], version=4)  # Ensure the ID is a valid UUID
        assert body["json"]["name"] == "John Doe"
        assert body["json"]["email"] == "john.doe@example.com"
        assert body["json"]["is_active"] is False
        assert "password" not in body["json"]  # Ensure there are no fields with 'password' in the response
        assert body["json"]["roles"] == ["cliente"]
    
    def test_add_client_route_email_already_exist(self, client: TestClient, tst_db_session, make_user, seed_roles):
        # Create a user first to ensure the email already exists
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"

        user = make_user(
            name="John Doe",
            email="john.doe@example.com",
            is_active=False,
            activation_code=hasher.hash(raw_code),
            activation_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            roles={"cliente"},
        )
        repository.add_user(user=user)



        # Now attempt to add another user with the same email
        response = client.post("/users/clients/", json={
            "name": "John Smith",
            "email": "john.doe@example.com",
            "password": "anothersecurepassword"
        })
        assert response.status_code == 409  
        assert response.json() == {"detail": "User with email john.doe@example.com already exists"}

    def test_add_client_route_invalid_email(self, client: TestClient, tst_db_session, make_user, seed_roles):
        response = client.post("/users/clients/", json={
			"name": "John Doe",
			"email": "john.doeexample.com",
			"password": "securepassword"
		})
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body
        assert len(body["detail"]) > 0
        assert body["detail"][0]["msg"] == "value is not a valid email address"
        assert body["detail"][0]["loc"] == ["body", "email"]

    def test_add_client_route_password_empty(self, client: TestClient, tst_db_session, make_user, seed_roles):
        response = client.post("/users/clients/", json={
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": ""
        })
        assert response.status_code == 422  # Expecting a validation error due to empty password
        body = response.json()
        assert "detail" in body
        assert len(body["detail"]) > 0
        assert body["detail"][0]["msg"] == "ensure this value has at least 8 characters"
        assert body["detail"][0]["type"] == "value_error.any_str.min_length"
        
        assert body["detail"][0]["loc"] == ["body", "password"]
