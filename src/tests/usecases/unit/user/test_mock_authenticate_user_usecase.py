import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from domain.user.user_exceptions import InvalidCredentialsError, UserNotFoundError
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.security.token_service_interface import TokenServiceInterface
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.authenticate_user.authenticate_user_dto import (
    AuthenticateUserInputDTO,
)
from usecases.user.authenticate_user.authenticate_user_usecase import (
    AuthenticateUserUseCase,
)

from domain.security.token_service_dto import CreateAccessTokenDTO


class TestMockAuthenticateUserUsecase:
    # BEGIN: Test for successful authentication
    def test_authenticate_user_success(self):
        # Arrange
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_password_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_token_service = MagicMock(spec=TokenServiceInterface)

        user_id = uuid4()
        email_in = "john@example.com"

        mock_user_repository.find_user_by_email.return_value = User(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )

        mock_password_hasher.verify.return_value = True
        mock_token_service.create_access_token.return_value = "access_token"

        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            tokenService=mock_token_service,
        )

        input_dto = AuthenticateUserInputDTO(email=email_in, password="test_password")

        # Act
        result = use_case.execute(input_dto)

        # Assert
        mock_user_repository.find_user_by_email.assert_called_once_with(email=email_in)
        mock_password_hasher.verify.assert_called_once_with(
            password="test_password", hashed_password="hashed_password"
        )
        data = CreateAccessTokenDTO(sub=user_id, email=email_in, roles=["cliente"])
        mock_token_service.create_access_token.assert_called_once_with(data = data)
        assert result.access_token == "access_token"
        assert result.token_type == "bearer"
        called_arg = mock_token_service.create_access_token.call_args.kwargs["data"]
        assert isinstance(called_arg, CreateAccessTokenDTO)
        assert called_arg.sub == user_id
        assert called_arg.email == email_in
        assert called_arg.roles == ["cliente"]

    # END: Test for successful authentication

    # BEGIN: Test for user not found
    def test_authenticate_user_user_not_found(self):
        # Arrange
        mock_user_repository = MagicMock()
        mock_password_hasher = MagicMock()
        mock_token_service = MagicMock()
        email_in = "non_existent_user@example.com"

        mock_user_repository.find_user_by_email.side_effect = UserNotFoundError(
            email_in
        )

        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            tokenService=mock_token_service,
        )

        input_dto = AuthenticateUserInputDTO(email=email_in, password="test_password")

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)
        mock_user_repository.find_user_by_email.assert_called_once_with(email=email_in)

        mock_password_hasher.verify.assert_not_called()
        mock_token_service.create_access_token.assert_not_called()

    # # END: Test for user not found

    # BEGIN: Test for inactive user
    def test_authenticate_user_inactive_user(self):
        # Arrange
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_password_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_token_service = MagicMock(spec=TokenServiceInterface)

        user_id = uuid4()
        email_in = "john@example.com"

        mock_user_repository.find_user_by_email.return_value = User(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password="hashed_password",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )

        mock_password_hasher.verify.return_value = True
        mock_token_service.create_access_token.return_value = "access_token"

        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            tokenService=mock_token_service,
        )

        input_dto = AuthenticateUserInputDTO(email=email_in, password="test_password")

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

        mock_user_repository.find_user_by_email.assert_called_once_with(email=email_in)
        mock_password_hasher.verify.assert_not_called()
        mock_token_service.create_access_token.assert_not_called()

    # END: Test for inactive user

    # BEGIN: Test for invalid password
    def test_authenticate_user_invalid_password(self):
        # Arrange
        # Arrange
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_password_hasher = MagicMock(spec=PasswordHasherInterface)
        mock_token_service = MagicMock(spec=TokenServiceInterface)

        user_id = uuid4()
        email_in = "john@example.com"

        mock_user_repository.find_user_by_email.return_value = User(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        mock_password_hasher.verify.return_value = False

        use_case = AuthenticateUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            tokenService=mock_token_service,
        )

        input_dto = AuthenticateUserInputDTO(email=email_in, password="wrong_password")

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

        mock_user_repository.find_user_by_email.assert_called_once_with(email=email_in)
        mock_password_hasher.verify.assert_called_once_with(
            password="wrong_password", hashed_password="hashed_password"
        )
        mock_token_service.create_access_token.assert_not_called()

    # END: Test for invalid password
