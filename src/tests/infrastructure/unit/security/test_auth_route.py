import infrastructure.api.security.get_current_token as get_current_token_module

from uuid import uuid4
from fastapi.testclient import TestClient

from domain.security.security_exceptions import ExpiredTokenError, InvalidTokenError
from domain.security.token_service_dto import TokenPayloadDTO
from infrastructure.user.sqlalchemy.user_repository import userRepository


class FakeExpiredTokenService:
    def decode_token(self, token: str) -> TokenPayloadDTO:
        raise ExpiredTokenError()


class FakeInvalidTokenService:
    def decode_token(self, token: str) -> TokenPayloadDTO:
        raise InvalidTokenError()


class FakeValidTokenService:
    def __init__(self, user_id, email, roles):
        self.user_id = user_id
        self.email = email
        self.roles = roles

    def decode_token(self, token: str) -> TokenPayloadDTO:
        return TokenPayloadDTO(
            sub=self.user_id,
            email=self.email,
            roles=sorted(map(str, self.roles)),
        )


class TestListMyServiceRequestsAuthRoute:
    def test_list_my_service_requests_with_expired_token_returns_401(
        self,
        client: TestClient,
        monkeypatch,
    ):
        monkeypatch.setattr(
            get_current_token_module,
            "make_token_service",
            lambda: FakeExpiredTokenService(),
        )

        response = client.get(
            "/user-service-requests/me",
            headers={"Authorization": "Bearer expired-token"},
        )

        assert response.status_code == 401
        body = response.json()
        assert "detail" in body
        assert "expired" in body["detail"].lower()

    def test_list_my_service_requests_with_invalid_token_returns_401(
        self,
        client: TestClient,
        monkeypatch,
    ):
        monkeypatch.setattr(
            get_current_token_module,
            "make_token_service",
            lambda: FakeInvalidTokenService(),
        )

        response = client.get(
            "/user-service-requests/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        body = response.json()
        assert "detail" in body

    def test_list_my_service_requests_without_token_returns_401(
        self,
        client: TestClient,
    ):
        response = client.get("/user-service-requests/me")

        assert response.status_code == 401
        body = response.json()
        assert "detail" in body

    def test_list_my_service_requests_with_valid_token_returns_200(
        self,
        client: TestClient,
        tst_db_session,
        make_user,
        seed_roles,
        monkeypatch,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user_id = uuid4()
        email = "john@example.com"
        roles = {"cliente"}

        user = make_user(
            id=user_id,
            name="John Doe",
            email=email,
            hashed_password="hashed-password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles=roles,
        )
        user_repository.add_user(user=user)

        monkeypatch.setattr(
            get_current_token_module,
            "make_token_service",
            lambda: FakeValidTokenService(
                user_id=user_id,
                email=email,
                roles=roles,
            ),
        )

        response = client.get(
            "/user-service-requests/me",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
