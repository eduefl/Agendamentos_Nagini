

from infrastructure.security.settings import get_settings
from infrastructure.security.token_service import TokenService


def make_token_service() -> TokenService:
    settings = get_settings()

    return TokenService(
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expire_minutes=settings.access_token_expire_minutes,
    )