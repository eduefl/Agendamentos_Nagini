from uuid import UUID

import pytest

from domain.user.user_exceptions import EmailAlreadyExistsError
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.fakes.fake_email_sender import FakeEmailSender
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO, AddClientOutputDTO
from usecases.user.add_user.add_cliente_usecase import AddClientUseCase


class TestAddClientUseCaseIntegration:
    def test_create_client_valid_persists_user_and_assigns_cliente_role(self, tst_db_session):
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

        assert len(fake_email_sender.sent_emails) == 1
        to_email, activation_code = fake_email_sender.sent_emails[0]
        assert to_email == "john.client@example.com"
        assert activation_code is not None
        assert activation_code != ""
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
        assert found.activation_code is not None
        assert found.activation_code != ""
        assert found.activation_code_expires_at is not None
        # assert found.activation_code == activation_code
        assert hasher.verify(activation_code,found.activation_code)

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
        assert len(fake_email_sender.sent_emails) == 1
        assert fake_email_sender.sent_emails[0][0] == "dup.client@example.com"

        with pytest.raises(EmailAlreadyExistsError, match="dup.client@example.com"):
            use_case.execute(input=input2)

        users = repository.list_users()
        assert len(users) == 1
        assert users[0].email == "dup.client@example.com"
        assert users[0].roles == {"cliente"}
        assert users[0].is_active is False

        assert len(fake_email_sender.sent_emails) == 1