from datetime import datetime, timedelta, timezone
from jose import JWTError, ExpiredSignatureError, jwt

from domain.security.token_service_dto import CreateAccessTokenDTO, TokenPayloadDTO
from domain.security.security_exceptions import ExpiredTokenError, InvalidTokenError
from domain.security.token_service_interface import TokenServiceInterface
from uuid import UUID


class TokenService(TokenServiceInterface):
    def __init__(self, secret_key: str, algorithm: str, expire_minutes: int):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create_access_token(self, data: CreateAccessTokenDTO) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": str(data.sub),
            "email": str(data.email),
            "roles": list(data.roles),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> TokenPayloadDTO:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except ExpiredSignatureError as exc:
            raise ExpiredTokenError() from exc
        except JWTError as exc:
            raise InvalidTokenError() from exc

        strsub = payload.get("sub")
        try:
            sub = UUID(strsub) if strsub else None
        except ValueError:
            raise InvalidTokenError()
        if not sub:
            raise InvalidTokenError()
        email = payload.get("email")
        if not email:
            raise InvalidTokenError()
        roles = payload.get("roles")
        if roles is None:
            roles = []
        if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
            raise InvalidTokenError()

        return TokenPayloadDTO(
            sub=sub,
            email=payload.get("email"),
            roles=roles,
        )
