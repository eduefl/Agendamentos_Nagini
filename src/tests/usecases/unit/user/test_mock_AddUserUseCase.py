import pytest
from unittest.mock import MagicMock
from uuid import UUID

from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_exceptions import EmailAlreadyExistsError, RoleNotFoundError, RolesRequiredError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_user_dto import AddUserInputDTO, AddUserOutputDTO
from usecases.user.add_user.add_user_usecase import AddUserUseCase


class TestAddUserUseCase:
    def test_mock_create_user_valid(self):
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_hasher.hash.return_value = "hashed-password"

        use_case = AddUserUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
            role="cliente",
        )

        output = use_case.execute(input=input_dto)

        assert output.id is not None
        assert isinstance(output, AddUserOutputDTO)
        assert isinstance(output.id, UUID)
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is True
        assert output.roles == ["cliente"]

        mock_hasher.hash.assert_called_once_with("12345678")
        mock_repository.add_user.assert_called_once()

        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.id == output.id
        assert user_sent.name == "John Doe"
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed-password"
        assert user_sent.is_active is True
        assert user_sent.roles == {"cliente"}

    def test_mock_add_user_raises_email_already_exists(self):
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_hasher.hash.return_value = "hashed-password"

        # o repositório simula o erro de email duplicado
        mock_repository.add_user.side_effect = EmailAlreadyExistsError("john@example.com")

        use_case = AddUserUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
            role="cliente",
        )

        with pytest.raises(EmailAlreadyExistsError, match="john@example.com"):
            use_case.execute(input=input_dto)

        # mesmo falhando, o hasher e o repo foram chamados
        mock_hasher.hash.assert_called_once_with("12345678")
        mock_repository.add_user.assert_called_once()

        # opcional: validar o user enviado ao repo
        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed-password"
        assert user_sent.is_active is True
        assert user_sent.roles == {"cliente"}

    def test_mock_add_user_raises_roles_required(self):
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_hasher.hash.return_value = "hashed-password"

        # simula regra do repositório: roles obrigatórios
        mock_repository.add_user.side_effect = RolesRequiredError()

        use_case = AddUserUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
            role="cliente",
        )

        with pytest.raises(RolesRequiredError, match="User roles are required"):
            use_case.execute(input=input_dto)

        mock_hasher.hash.assert_called_once_with("12345678")
        mock_repository.add_user.assert_called_once()

        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed-password"
        assert user_sent.is_active is True
        # importante: mesmo com erro, o UseCase enviou roles corretamente
        assert user_sent.roles == {"cliente"}        

    def test_mock_add_user_raises_role_not_found(self):
        mock_repository = MagicMock(spec=userRepositoryInterface)

        mock_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_hasher.hash.return_value = "hashed-password"

        # simula regra do repositório: role não existe no banco
        mock_repository.add_user.side_effect = RoleNotFoundError("inexistente")

        use_case = AddUserUseCase(
            user_repository=mock_repository,
            password_hasher=mock_hasher,
        )

        input_dto = AddUserInputDTO(
            name="John Doe",
            email="john@example.com",
            password="12345678",
            role="inexistente",
        )

        with pytest.raises(RoleNotFoundError, match="inexistente"):
            use_case.execute(input=input_dto)

        mock_hasher.hash.assert_called_once_with("12345678")
        mock_repository.add_user.assert_called_once()

        user_sent = mock_repository.add_user.call_args.kwargs["user"]
        assert user_sent.email == "john@example.com"
        assert user_sent.hashed_password == "hashed-password"
        assert user_sent.is_active is True
        assert user_sent.roles == {"inexistente"}