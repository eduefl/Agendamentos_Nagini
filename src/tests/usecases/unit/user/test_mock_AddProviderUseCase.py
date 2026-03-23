from unittest.mock import MagicMock
from uuid import UUID

from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_prestador_dto import AddPrestadorInputDTO, AddPrestadorOutputDTO
from usecases.user.add_user.add_prestador_usecase import AddPrestadorUseCase


class TestAddProviderUseCase:
    def test_mock_create_provider_valid_sets_inactive_and_provider_role(self):
        # Arrange
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_hasher.hash.return_value = "hashed-password"

        use_case = AddPrestadorUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
        )

        input_dto = AddPrestadorInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, AddPrestadorOutputDTO)
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is False
        assert output.roles == ["prestador"]

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
        assert user_sent.roles == {"prestador"}
        assert user_sent.activation_code is None
        assert user_sent.activation_code_expires_at is None