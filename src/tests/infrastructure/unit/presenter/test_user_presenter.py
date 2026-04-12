"""
Testes para UserPresenter cobrindo todos os métodos toJSON e toXml.
"""

import pytest
from uuid import uuid4

from infrastructure.presenters.user_presenter import UserPresenter, _normalize_roles, _pydantic_to_dict
from usecases.user.add_user.add_user_dto import AddUserOutputDTO
from usecases.user.add_user.add_cliente_dto import AddClientOutputDTO
from usecases.user.add_user.add_prestador_dto import AddPrestadorOutputDTO
from usecases.user.activate_user.activate_user_dto import ActivateUserOutputDTO
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdOutputDTO
from usecases.user.list_users.list_users_dto import ListUsersOutputDTO, UserDto
from usecases.user.update_user.update_user_dto import UpdateUserOutputDTO


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_find_user_dto():
    return findUserByIdOutputDTO(
        id=uuid4(),
        name="Ana Silva",
        email="ana@example.com",
        is_active=True,
        roles=["cliente"],
    )


def _make_add_user_dto():
    return AddUserOutputDTO(
        id=uuid4(),
        name="João",
        email="joao@example.com",
        is_active=False,
        roles=["cliente"],
    )


def _make_add_client_dto():
    return AddClientOutputDTO(
        id=uuid4(),
        name="Maria",
        email="maria@example.com",
        is_active=False,
        roles=["cliente"],
    )


def _make_add_prestador_dto():
    return AddPrestadorOutputDTO(
        id=uuid4(),
        name="Pedro",
        email="pedro@example.com",
        is_active=False,
        roles=["prestador"],
    )


def _make_activate_dto():
    return ActivateUserOutputDTO(
        id=uuid4(),
        name="Lucas",
        email="lucas@example.com",
        is_active=True,
        roles=["cliente"],
    )


def _make_update_dto():
    return UpdateUserOutputDTO(
        id=uuid4(),
        name="Carlos",
        email="carlos@example.com",
        is_active=True,
        roles=["cliente", "prestador"],
    )


def _make_list_users_dto(count=2):
    users = [
        UserDto(
            id=uuid4(),
            name=f"User {i}",
            email=f"user{i}@example.com",
            is_active=True,
            roles=["cliente"],
        )
        for i in range(count)
    ]
    return ListUsersOutputDTO(users=users)


# ─── _normalize_roles ────────────────────────────────────────────────────────

class TestNormalizeRoles:
    def test_returns_none_when_roles_is_none(self):
        assert _normalize_roles(None) is None

    def test_returns_sorted_list(self):
        result = _normalize_roles(["prestador", "cliente"])
        assert result == ["cliente", "prestador"]

    def test_returns_empty_list_when_empty(self):
        assert _normalize_roles([]) == []


# ─── _pydantic_to_dict ───────────────────────────────────────────────────────

class TestPydanticToDict:
    def test_uses_model_dump_when_available(self):
        dto = _make_find_user_dto()
        result = _pydantic_to_dict(dto)
        assert isinstance(result, dict)
        assert "id" in result

    def test_fallback_dict_method(self):
        class _LegacyModel:
            def dict(self):
                return {"legacy": True}

        result = _pydantic_to_dict(_LegacyModel())
        assert result == {"legacy": True}

    def test_fallback_dict_conversion(self):
        result = _pydantic_to_dict({"key": "value"})
        assert result == {"key": "value"}


# ─── toJSON ──────────────────────────────────────────────────────────────────

class TestUserPresenterToJSON:
    def test_find_user_dto(self):
        dto = _make_find_user_dto()
        result = UserPresenter.toJSON(dto)
        assert result["name"] == "Ana Silva"
        assert result["email"] == "ana@example.com"
        assert result["is_active"] is True
        assert "cliente" in result["roles"]

    def test_add_user_dto(self):
        dto = _make_add_user_dto()
        result = UserPresenter.toJSON(dto)
        assert result["name"] == "João"

    def test_add_client_dto(self):
        dto = _make_add_client_dto()
        result = UserPresenter.toJSON(dto)
        assert result["name"] == "Maria"
        assert "cliente" in result["roles"]

    def test_add_prestador_dto(self):
        dto = _make_add_prestador_dto()
        result = UserPresenter.toJSON(dto)
        assert result["name"] == "Pedro"
        assert "prestador" in result["roles"]

    def test_activate_user_dto(self):
        dto = _make_activate_dto()
        result = UserPresenter.toJSON(dto)
        assert result["is_active"] is True

    def test_update_user_dto(self):
        dto = _make_update_dto()
        result = UserPresenter.toJSON(dto)
        assert result["name"] == "Carlos"
        assert sorted(result["roles"]) == ["cliente", "prestador"]

    def test_list_users_dto(self):
        dto = _make_list_users_dto(count=2)
        result = UserPresenter.toJSON(dto)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_unsupported_type_raises(self):
        with pytest.raises(NotImplementedError):
            UserPresenter.toJSON(object())


# ─── toXml ───────────────────────────────────────────────────────────────────

class TestUserPresenterToXml:
    def test_find_user_dto(self):
        dto = _make_find_user_dto()
        result = UserPresenter.toXml(dto)
        assert "Ana Silva" in result
        assert "<user>" in result

    def test_add_user_dto(self):
        dto = _make_add_user_dto()
        result = UserPresenter.toXml(dto)
        assert "João" in result

    def test_add_client_dto(self):
        dto = _make_add_client_dto()
        result = UserPresenter.toXml(dto)
        assert "Maria" in result

    def test_add_prestador_dto(self):
        dto = _make_add_prestador_dto()
        result = UserPresenter.toXml(dto)
        assert "Pedro" in result

    def test_activate_user_dto(self):
        dto = _make_activate_dto()
        result = UserPresenter.toXml(dto)
        assert "Lucas" in result

    def test_update_user_dto(self):
        dto = _make_update_dto()
        result = UserPresenter.toXml(dto)
        assert "Carlos" in result

    def test_list_users_dto(self):
        dto = _make_list_users_dto(count=2)
        result = UserPresenter.toXml(dto)
        assert "<data>" in result
        assert result.count("<user>") == 2

    def test_unsupported_type_raises(self):
        with pytest.raises(NotImplementedError):
            UserPresenter.toXml(object())