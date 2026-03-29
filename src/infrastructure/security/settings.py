from dataclasses import dataclass
from functools import lru_cache
import os

from domain.security.security_exceptions import SettingsError




@dataclass(frozen=True)
class Settings:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


@lru_cache
def get_settings() -> Settings:
    secret_key = os.getenv("CHAVE_SECRETA")
    algorithm = os.getenv("ALGORITMO")
    expire_minutes_raw = os.getenv("TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO")

    if not secret_key:
        raise SettingsError("CHAVE_SECRETA não configurada")
    if not algorithm:
        raise SettingsError("ALGORITMO não configurado")
    if not expire_minutes_raw:
        raise SettingsError("TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO não configurado")

    try:
        expire_minutes = int(expire_minutes_raw)
    except ValueError as exc:
        raise SettingsError(
            "TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO deve ser um inteiro"
        ) from exc

    if expire_minutes <= 0:
        raise SettingsError(
            "TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO deve ser maior que zero"
        )

    return Settings(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_expire_minutes=expire_minutes,
    )