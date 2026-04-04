import os
import pytest
from infrastructure.security.settings import get_settings, SettingsError


class TestGetSettings:
    @pytest.fixture(autouse=True)
    def setup(self):
        original_env = dict(os.environ)
        get_settings.cache_clear()

        yield

        os.environ.clear()
        os.environ.update(original_env)
        get_settings.cache_clear()

    def test_get_settings_success(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "15"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "30"

        settings = get_settings()
        assert settings.secret_key == "test_secret"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 15
        assert settings.expire_minutes_request == 30

    def test_get_settings_missing_secret_key(self):
        os.environ.pop("CHAVE_SECRETA", None)
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "15"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "30"

        with pytest.raises(SettingsError, match="CHAVE_SECRETA não configurada"):
            get_settings()

    def test_get_settings_missing_algorithm(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ.pop("ALGORITMO", None)
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "15"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "30"

        with pytest.raises(SettingsError, match="ALGORITMO não configurado"):
            get_settings()

    def test_get_settings_missing_expire_access_minutes(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ.pop("TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO", None)
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "30"

        with pytest.raises(
            SettingsError,
            match="TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO não configurado",
        ):
            get_settings()

    def test_get_settings_invalid_expire_minutes(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "invalid"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "30"

        with pytest.raises(
            SettingsError,
            match="TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO deve ser um inteiro",
        ):
            get_settings()

    def test_get_settings_expire_minutes_zero(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "0"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "30"

        with pytest.raises(
            SettingsError,
            match="TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO deve ser maior que zero",
        ):
            get_settings()


    def test_get_settings_missing_expire_request_minutes(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "15"
        os.environ.pop("TEMPO_DE_EXPIRACAO_SOLICITACAO", None)

        with pytest.raises(
            SettingsError,
            match="TEMPO_DE_EXPIRACAO_SOLICITACAO não configurado",
        ):
            get_settings()

    def test_get_settings_invalid_expire_request_minutes(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "15"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "invalid"

        with pytest.raises(
            SettingsError,
            match="TEMPO_DE_EXPIRACAO_SOLICITACAO deve ser um inteiro",
        ):
            get_settings()

    def test_get_settings_expire_request_minutes_zero(self):
        os.environ["CHAVE_SECRETA"] = "test_secret"
        os.environ["ALGORITMO"] = "HS256"
        os.environ["TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO"] = "15"
        os.environ["TEMPO_DE_EXPIRACAO_SOLICITACAO"] = "0"

        with pytest.raises(
            SettingsError,
            match="TEMPO_DE_EXPIRACAO_SOLICITACAO deve ser maior que zero",
        ):
            get_settings()
