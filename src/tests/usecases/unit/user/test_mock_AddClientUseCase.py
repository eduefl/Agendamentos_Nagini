import pytest
from unittest.mock import MagicMock
from uuid import UUID

from domain.notification.email_sender_interface import EmailSenderInterface
from domain.notification.notification_exceptions import EmailDeliveryError
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO, AddClientOutputDTO
from usecases.user.add_user.add_cliente_usecase import AddClientUseCase


class TestAddClientUseCase:
    def test_mock_create_client_valid_sets_inactive_and_cliente_role(self):
        mock_repository = MagicMock(spec=userRepositoryInterface)
        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_email_sender = MagicMock(spec=EmailSenderInterface)

        # mock_hasher.hash.return_value = "hashed-password"
        mock_hasher.hash.side_effect = lambda value: f"hashed::{value}"

        use_case = AddClientUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
            email_sender=mock_email_sender,  # Passa o mock do EmailSenderInterface 
        )

        input_dto = AddClientInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, AddClientOutputDTO)
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is False
        assert output.roles == ["cliente"]

        # Assert (collaborators)

        assert mock_hasher.hash.call_count == 2
        mock_hasher.hash.assert_any_call("12345678")
        mock_repository.add_user.assert_called_once()
        mock_email_sender.send_activation_email.assert_called_once()

        # Assert (user sent to repository)
        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.id == output.id
        assert user_sent.name == "John Doe"
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed::12345678"
        assert user_sent.is_active is False
        assert user_sent.roles == {"cliente"}
        assert user_sent.activation_code is not None
        assert user_sent.activation_code != ""
        assert user_sent.activation_code_expires_at is not None

        args = mock_email_sender.send_activation_email.call_args.args
        assert args[0] == "john@example.com"
        assert user_sent.activation_code != args[1]
        assert user_sent.activation_code.startswith("hashed::")

    def test_mock_create_client_raises_when_email_delivery_fails_after_persisting_user(self):
        # Arrange
        mock_repository = MagicMock(spec=userRepositoryInterface)
        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_email_sender = MagicMock(spec=EmailSenderInterface)

        mock_hasher.hash.return_value = "hashed-password"
        mock_email_sender.send_activation_email.side_effect = EmailDeliveryError(
            "Falha ao enviar email de ativação"
        )

        use_case = AddClientUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
            email_sender=mock_email_sender,  # Passa o mock do EmailSenderInterface 
        )

        input_dto = AddClientInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
        )

        # Act
        with pytest.raises(EmailDeliveryError) as exc_info:
            use_case.execute(input=input_dto)

        assert str(exc_info.value) == "Falha ao enviar email de ativação"
        assert mock_repository.add_user.call_count == 1
        assert mock_email_sender.send_activation_email.call_count == 1

        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.email == "john@example.com"
        assert user_sent.is_active is False
        assert user_sent.roles == {"cliente"}
        assert user_sent.activation_code is not None
        assert user_sent.activation_code_expires_at is not None