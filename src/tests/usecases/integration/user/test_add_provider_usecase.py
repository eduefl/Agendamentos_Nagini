
from usecases.user.add_user.add_prestador_dto import AddPrestadorInputDTO, AddPrestadorOutputDTO
from usecases.user.add_user.add_prestador_usecase import AddPrestadorUseCase
import pytest
from uuid import UUID

from domain.user.user_exceptions import EmailAlreadyExistsError
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestAddProviderUseCaseIntegration:
    def test_create_provider_valid_persists_user_and_assigns_provider_role(self, tst_db_session):
        # Arrange
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddPrestadorUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = AddPrestadorInputDTO(
            name="John Doe",
            email="john.provieder@example.com",
            password="12345678",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, AddPrestadorOutputDTO)
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john.provieder@example.com"
        assert output.is_active is False
        assert output.roles == ["prestador"]

        # Assert (persisted)
        found = repository.find_user_by_id(user_id=output.id)
        assert found.id == output.id
        assert found.name == "John Doe"
        assert found.email == "john.provieder@example.com"
        assert found.is_active is False
        assert isinstance(found.hashed_password, str)
        assert found.hashed_password != ""
        assert found.hashed_password != "12345678"

        # role associada via tabela tb_user_roles
        assert found.roles == {"prestador"}

    def test_create_provider_raises_email_already_exists_when_duplicate_email(
        self, tst_db_session
    ):
        # Arrange
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = AddPrestadorUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        # mesmo email nas duas tentativas
        input1 = AddPrestadorInputDTO(
            name="Prestador 1",
            email="dup.prestador@example.com",
            password="12345678",
        )
        input2 = AddPrestadorInputDTO(
            name="Prestador 2",
            email="dup.prestador@example.com",
            password="87654321",
        )

        # Act
        out1 = use_case.execute(input=input1)

        # Assert
        assert str(out1.email) == "dup.prestador@example.com"
        assert out1.roles == ["prestador"]
        assert out1.is_active is False

        with pytest.raises(EmailAlreadyExistsError, match="dup.prestador@example.com"):
            use_case.execute(input=input2)

        # garante que só 1 usuário existe no banco
        users = repository.list_users()
        assert len(users) == 1
        assert users[0].email == "dup.prestador@example.com"
        assert users[0].roles == {"prestador"}
        assert users[0].is_active is False