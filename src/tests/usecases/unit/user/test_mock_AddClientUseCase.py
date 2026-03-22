from unittest.mock import MagicMock
from uuid import UUID

from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO, AddClientOutputDTO
from usecases.user.add_user.add_cliente_usecase import AddClientUseCase


class TestAddClientUseCase:
    def test_mock_create_client_valid_sets_inactive_and_cliente_role(self):
        # Arrange
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_hasher.hash.return_value = "hashed-password"

        use_case = AddClientUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
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

        # Assert (user sent to repository)
        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.id == output.id
        assert user_sent.name == "John Doe"
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed-password"
        assert user_sent.is_active is False
        assert user_sent.roles == {"cliente"}