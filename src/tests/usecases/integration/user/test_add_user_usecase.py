import pytest
from uuid import UUID

from domain.user.user_exceptions import EmailAlreadyExistsError
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_user_dto import AddUserInputDTO, AddUserOutputDTO
from usecases.user.add_user.add_user_usecase import AddUserUseCase


class TestAddUserUseCase:
    def test_create_user_valid(self, tst_db_session):
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
        )

        output = use_case.execute(input=input_dto)

        assert isinstance(output, AddUserOutputDTO)
        assert output.id is not None
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john.doe@example.com"
        assert output.is_active is True

        assert len(repository.list_users()) == 1

        found = repository.find_user_by_id(user_id=output.id)
        assert found.id == output.id
        assert found.name == "John Doe"
        assert found.email == "john.doe@example.com"
        assert found.is_active is True
        assert isinstance(found.hashed_password, str)
        assert found.hashed_password != ""

    def test_create_user_raises_email_already_exists(self, tst_db_session):
        session = tst_db_session

        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        # mesmo email nas duas tentativas
        input1 = AddUserInputDTO(
            name="John Doe",
            email="dup@example.com",
            password="12345678",
        )
        input2 = AddUserInputDTO(
            name="Jane Doe",
            email="dup@example.com",
            password="87654321",
        )

        out1 = use_case.execute(input=input1)
        assert out1.id is not None

        with pytest.raises(EmailAlreadyExistsError, match="dup@example.com"):
            use_case.execute(input=input2)

        # garante que não inseriu o segundo usuário
        users = repository.list_users()
        assert len(users) == 1
        assert users[0].email == "dup@example.com"