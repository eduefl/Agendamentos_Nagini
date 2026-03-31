from uuid import uuid4
from datetime import datetime, timedelta

import pytest


class TestUser:
    def test_user_initialization(self, make_user):
        user_id = uuid4()
        user_name = "John Doe"
        user_email = "john@example.com"
        user_hashed_password = "hashed-password"

        user = make_user(
            id=user_id,
            name=user_name,
            email=user_email,
            hashed_password=user_hashed_password,
            roles={"prestador"},
        )

        assert user.id == user_id
        assert user.name == user_name
        assert user.email == user_email
        assert user.hashed_password == user_hashed_password
        assert user.is_active is False
        assert user.tasks == []
        assert user.roles == {"prestador"}

    def test_user_id_validation(self, make_user):
        with pytest.raises(ValueError, match="ID must be a valid UUID."):
            make_user(id="invalid-uuid")

    def test_user_name_validation_type(self, make_user):
        with pytest.raises(ValueError, match="Name must be a string."):
            make_user(name=4)

    def test_user_name_validation_empty(self, make_user):
        with pytest.raises(ValueError, match="Name cannot be empty."):
            make_user(name="")

    def test_user_name_validation_blank(self, make_user):
        with pytest.raises(ValueError, match="Name cannot be empty."):
            make_user(name="       ")

    def test_user_email_validation_type(self, make_user):
        with pytest.raises(ValueError, match="Email must be a string."):
            make_user(email=123)

    def test_user_email_validation_empty(self, make_user):
        with pytest.raises(ValueError, match="Email cannot be empty."):
            make_user(email="")

    def test_user_email_validation_blank(self, make_user):
        with pytest.raises(ValueError, match="Email cannot be empty."):
            make_user(email="   ")

    def test_user_email_validation_spaces(self, make_user):
        with pytest.raises(ValueError, match="Email cannot contain spaces."):
            make_user(email="john doe@example.com")

    def test_user_email_validation_format(self, make_user):
        with pytest.raises(ValueError, match="Email must be valid."):
            make_user(email="johnexample.com")

    def test_user_hashed_password_validation_type(self, make_user):
        with pytest.raises(ValueError, match="Hashed password must be a string."):
            make_user(hashed_password=123)

    def test_user_hashed_password_validation_empty(self, make_user):
        with pytest.raises(ValueError, match="Hashed password cannot be empty."):
            make_user(hashed_password="")

    def test_user_is_active_validation_type(self, make_user):
        with pytest.raises(ValueError, match="is_active must be a boolean."):
            make_user(is_active="true")

    # --- roles tests (novos) ---
    def test_user_roles_normalization(self, make_user):
        user = make_user(roles=[" Cliente ", "ADMIN"])
        assert user.roles == {"cliente", "admin"}

    def test_user_roles_must_be_iterable_of_strings(self, make_user):
        with pytest.raises(ValueError, match="Each role must be a string."):
            make_user(roles=[123])

    def test_user_roles_cannot_be_empty_string(self, make_user):
        with pytest.raises(ValueError, match="Role cannot be empty."):
            make_user(roles=[""])

    def test_user_roles_cannot_be_blank(self, make_user):
        with pytest.raises(ValueError, match="Role cannot be empty."):
            make_user(roles=["   "])

    def test_user_roles_cannot_contain_spaces(self, make_user):
        with pytest.raises(ValueError, match="Role cannot contain spaces."):
            make_user(roles=["admin user"])

    def test_user_initialization_sets_activation_fields_as_none(self, make_user):
        user = make_user(roles={"prestador"})
        assert user.is_active is False
        assert user.activation_code is None
        assert user.activation_code_expires_at is None

    def test_user_activation_code_requires_expiration(self, make_user):
        with pytest.raises(
            ValueError,
            match="Activation code expiration must be provided when activation code exists.",
        ):
            make_user(
                activation_code="abc12345",
                activation_code_expires_at=None,
            )

    def test_user_activation_expiration_requires_code(self, make_user):

        with pytest.raises(
            ValueError,
            match="Activation code must be provided when expiration exists.",
        ):
            make_user(
                activation_code=None,
                activation_code_expires_at=datetime.now(),
            )

    def test_set_activation_code(self, make_user):
        user = make_user()
        expires_at = datetime.now() + timedelta(minutes=15)

        user.set_activation_code("abc12345", expires_at)

        assert user.activation_code == "abc12345"
        assert user.activation_code_expires_at == expires_at

    def test_set_activation_code_with_invalid_expiration(self, make_user):
        user = make_user()

        with pytest.raises(
            ValueError,
            match="Activation code expiration must be provided when activation code exists.",
        ):
            user.set_activation_code("abc12345", None)

    def test_clear_activation_code(self, make_user):

        user = make_user()
        expires_at = datetime.now() + timedelta(minutes=15)

        user.set_activation_code("abc12345", expires_at)
        user.clear_activation_code()

        assert user.activation_code is None
        assert user.activation_code_expires_at is None

    def test_activate_user_clears_activation_data(self, make_user):

        user = make_user()
        expires_at = datetime.now() + timedelta(minutes=15)

        user.set_activation_code("abc12345", expires_at)
        user.activate()

        assert user.is_active is True
        assert user.activation_code is None
        assert user.activation_code_expires_at is None

    def test_set_activation_code_normalizes_code(self, make_user):
        from datetime import datetime, timedelta

        user = make_user()
        expires_at = datetime.now() + timedelta(minutes=15)

        user.set_activation_code("  abc12345  ", expires_at)

        assert user.activation_code == "abc12345"

    # tests para os métodos de gerenciamento de roles
    def test_add_role(self, make_user):
        user = make_user(roles={"cliente"})
        user.add_role("admin")
        assert "admin" in user.roles
        assert user.is_provider() is False
        user.add_role("prestador")
        assert user.is_provider() is True
