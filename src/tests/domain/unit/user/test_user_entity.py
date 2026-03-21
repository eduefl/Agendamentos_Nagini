from uuid import uuid4
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
            roles = {'prestador'}
        )

        assert user.id == user_id
        assert user.name == user_name
        assert user.email == user_email
        assert user.hashed_password == user_hashed_password
        assert user.is_active is True
        assert user.tasks == []
        assert user.roles == {'prestador'}  

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