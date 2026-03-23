import pytest
from uuid import UUID

from domain.user.user_exceptions import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    RolesRequiredError,
)
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_user_dto import AddUserInputDTO, AddUserOutputDTO
from usecases.user.add_user.add_user_usecase import AddUserUseCase


class _RepoRaisingRolesRequired(userRepository):
    """
    Repo wrapper para simular o mesmo cenário do teste mock:
    o repositório levanta RolesRequiredError, independentemente do que chegou.
    """
    def add_user(self, user):
        raise RolesRequiredError()


class TestAddUserUseCase:
    def test_create_user_valid(self, tst_db_session, seed_roles):
        session = tst_db_session

        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john.doe@example.com",
            password="12345678",
            role="cliente",
        )

        output = use_case.execute(input=input_dto)

        assert isinstance(output, AddUserOutputDTO)
        assert output.id is not None
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john.doe@example.com"
        assert output.is_active is False
        assert output.roles == ["cliente"]

        assert len(repository.list_users()) == 1

        found = repository.find_user_by_id(user_id=output.id)
        assert found.id == output.id
        assert found.name == "John Doe"
        assert found.email == "john.doe@example.com"
        assert found.is_active is False
        assert isinstance(found.hashed_password, str)
        assert found.hashed_password != ""
        assert found.roles == {"cliente"}
        assert found.activation_code is None
        assert found.activation_code_expires_at is None

    def test_create_user_raises_email_already_exists(self, tst_db_session, seed_roles):
        session = tst_db_session

        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input1 = AddUserInputDTO(
            name="John Doe",
            email="dup@example.com",
            password="12345678",
            role="cliente",
        )
        input2 = AddUserInputDTO(
            name="Jane Doe",
            email="dup@example.com",
            password="87654321",
            role="cliente",
        )

        out1 = use_case.execute(input=input1)
        assert out1.id is not None

        with pytest.raises(EmailAlreadyExistsError, match="dup@example.com"):
            use_case.execute(input=input2)

        users = repository.list_users()
        assert len(users) == 1
        assert users[0].email == "dup@example.com"
        assert users[0].roles == {"cliente"}
        assert users[0].is_active is False
        assert users[0].activation_code is None
        assert users[0].activation_code_expires_at is None

    def test_create_user_raises_roles_required(self, tst_db_session):
        """
        Equivalente ao teste mockado: repo levanta RolesRequiredError.
        Aqui a gente simula isso com um repo wrapper que sempre levanta.
        """
        session = tst_db_session

        repository = _RepoRaisingRolesRequired(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
            role="cliente",
        )

        with pytest.raises(RolesRequiredError, match="User roles are required"):
            use_case.execute(input=input_dto)

    def test_create_user_raises_role_not_found_when_role_does_not_exist(self, tst_db_session):
        session = tst_db_session

        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john.doe@example.com",
            password="12345678",
            role="inexistente",
        )

        with pytest.raises(RoleNotFoundError, match="inexistente"):
            use_case.execute(input=input_dto)