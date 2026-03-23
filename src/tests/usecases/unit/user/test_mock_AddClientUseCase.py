import pytest
from unittest.mock import MagicMock
from uuid import UUID

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.email_sender_interface import EmailSenderInterface
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO, AddClientOutputDTO
from usecases.user.add_user.add_cliente_usecase import AddClientUseCase


class TestAddClientUseCase:
    def test_mock_create_client_valid_sets_inactive_and_cliente_role(self):
        # Arrange
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_email_sender = MagicMock(spec=EmailSenderInterface)  # Mock para o EmailSenderInterface
        mock_hasher.hash.return_value = "hashed-password"

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
        mock_hasher.hash.assert_called_once_with("12345678")
        mock_repository.add_user.assert_called_once()
        mock_email_sender.send_activation_email. assert_called_once()

        # Assert (user sent to repository)
        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.id == output.id
        assert user_sent.name == "John Doe"
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed-password"
        assert user_sent.is_active is False
        assert user_sent.roles == {"cliente"}
    

    def test_mock_create_client_problem_sending_email(self):
        # Arrange
        mock_repository = MagicMock(spec=userRepositoryInterface)
        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_email_sender = MagicMock(spec=EmailSenderInterface)
        mock_hasher.hash.return_value = "hashed-password"
        mock_email_sender.send_activation_email.side_effect = EmailDeliveryError("Falha ao enviar email de ativação")

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
            output = use_case.execute(input=input_dto)
        
        # Assert
        assert str(exc_info.value) == "Falha ao enviar email de ativação"
        assert mock_email_sender.send_activation_email.call_count == 1
        assert mock_repository.add_user.call_count == 0
        

