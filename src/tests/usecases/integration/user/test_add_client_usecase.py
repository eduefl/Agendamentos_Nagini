
from tests.fakes.fake_email_sender import FakeEmailSender
import pytest
from uuid import UUID

from domain.user.user_exceptions import EmailAlreadyExistsError
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO, AddClientOutputDTO
from usecases.user.add_user.add_cliente_usecase import AddClientUseCase
from infrastructure.notification.smtp_email_sender import SMTPEmailSender


class TestAddClientUseCaseIntegration:
    def test_create_client_valid_persists_user_and_assigns_cliente_role(self, tst_db_session):
        # Arrange
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()
        fake_email_sender = FakeEmailSender()

        use_case = AddClientUseCase(
            user_repository=repository,
            password_hasher=hasher,
            email_sender=fake_email_sender,            
        )

        input_dto = AddClientInputDTO(
            name="John Doe",
            email="john.client@example.com",
            password="12345678",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, AddClientOutputDTO)
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john.client@example.com"
        assert output.is_active is False
        assert output.roles == ["cliente"]

        # Assert (persisted)
        found = repository.find_user_by_id(user_id=output.id)
        assert found.id == output.id
        assert found.name == "John Doe"
        assert found.email == "john.client@example.com"
        assert found.is_active is False
        assert isinstance(found.hashed_password, str)
        assert found.hashed_password != ""
        assert found.hashed_password != "12345678"

        # role associada via tabela tb_user_roles
        assert found.roles == {"cliente"}

    def test_create_client_raises_email_already_exists_when_duplicate_email(
        self, tst_db_session
    ):
        # Arrange
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()
        fake_email_sender = FakeEmailSender()

        


        use_case = AddClientUseCase(
            user_repository=repository,
            password_hasher=hasher,
            email_sender=fake_email_sender,            
        )

        # mesmo email nas duas tentativas
        input1 = AddClientInputDTO(
            name="Client 1",
            email="dup.client@example.com",
            password="12345678",
        )
        input2 = AddClientInputDTO(
            name="Client 2",
            email="dup.client@example.com",
            password="87654321",
        )

        # Act
        out1 = use_case.execute(input=input1)

        # Assert
        assert str(out1.email) == "dup.client@example.com"
        assert out1.roles == ["cliente"]
        assert out1.is_active is False

        with pytest.raises(EmailAlreadyExistsError, match="dup.client@example.com"):
            use_case.execute(input=input2)

        # garante que só 1 usuário existe no banco
        users = repository.list_users()
        assert len(users) == 1
        assert users[0].email == "dup.client@example.com"
        assert users[0].roles == {"cliente"}
        assert users[0].is_active is False