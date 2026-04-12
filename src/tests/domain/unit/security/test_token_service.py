from uuid import uuid4
from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.security.security_exceptions import ExpiredTokenError, InvalidTokenError
from infrastructure.security.token_service import TokenService
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import ValidationError
# from your_module import (
#     TokenService,
#     TokenPayloadDTO,
#     ExpiredTokenError,
#     InvalidTokenError,
# )  # Adjust the import as necessary


class TestTokenService:
    @pytest.fixture
    def token_service(self):
        return TokenService(
            secret_key="test_secret", algorithm="HS256", expire_minutes=15
        )

    def test_create_access_token(self, token_service):
        user_id = uuid4()
        data = CreateAccessTokenDTO(
            sub=user_id, email="user@example.com", roles=["usuario"]            
        )
        token = token_service.create_access_token(data)

        payload = jwt.decode(
            token, token_service._secret_key, algorithms=[token_service._algorithm]
        )
        assert payload["sub"] == str(data.sub)
        assert payload["email"] == data.email
        assert payload["roles"] == data.roles
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_token(self, token_service):
        user_id = uuid4()
        data = CreateAccessTokenDTO(
            sub=user_id, email="user@example.com"            
        )
        
        token = token_service.create_access_token(data)

        payload = token_service.decode_token(token)
        assert payload.sub == data.sub
        assert payload.email == data.email

    def test_decode_token_invalid(self, token_service):
        with pytest.raises(InvalidTokenError):
            token_service.decode_token("invalid_token")

    def test_decode_token_expired(self, token_service):
        user_id = str(uuid4())
        expired_token = jwt.encode(
            {
                "sub": user_id,
                "email": "user@example.com",
                "exp": int(
                    (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()
                ),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )

        with pytest.raises(ExpiredTokenError):
            token_service.decode_token(expired_token)

    def test_decode_token_missing_subject(self, token_service):
        token = jwt.encode(
            {
                "email": "user@example.com",
                "roles": [],
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )
        with pytest.raises(InvalidTokenError):
            token_service.decode_token(token)

    def test_decode_token_missing_email(self, token_service):
        user_id = str(uuid4())
        token = jwt.encode(
            {
                "sub": user_id,
                "roles": [],
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )

        with pytest.raises(InvalidTokenError):
            token_service.decode_token(token)

    def test_decode_token_invalidId_Sub(self, token_service):
        user_id = "USER_ID"
        token = jwt.encode(
            {
                "sub": user_id,
                "roles": [],
                "email":"user@example.com",
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )

        with pytest.raises(InvalidTokenError):
            token_service.decode_token(token)

    def test_create_access_token_dto_invalid_roles_type(self):
        with pytest.raises(ValidationError):
            CreateAccessTokenDTO(
                sub=uuid4(),
                email="user@example.com",
                roles=3,
            )


    def test_decode_token_invalid_roles_type(self, token_service):
        user_id = str(uuid4())
        token = jwt.encode(
            {
                "sub": user_id,
                "email": "user@example.com",
                "roles": 3,
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )

        with pytest.raises(InvalidTokenError):
            token_service.decode_token(token)

    def test_decode_token_invalid_roles_conttent(self, token_service):
        user_id = str(uuid4())
        token = jwt.encode(
            {
                "sub": user_id,
                "email": "user@example.com",
                "roles": ["usuario",3],
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )

        with pytest.raises(InvalidTokenError):
            token_service.decode_token(token)

    def test_decode_token_missing_roles_defaults_to_empty_list(self, token_service):
        user_id = str(uuid4())
        token = jwt.encode(
            {
                "sub": user_id,
                "email": "user@example.com",
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
            },
            token_service._secret_key,
            algorithm=token_service._algorithm,
        )

        payload = token_service.decode_token(token)
        assert payload.roles == []