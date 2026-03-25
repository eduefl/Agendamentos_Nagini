from datetime import datetime, timedelta
from domain.user.user_exceptions import ActivationCodeExpiredError, InvalidActivationCodeError, UserAlreadyActiveError, UserNotFoundError
from usecases.user.activate_user.activate_user_dto import ActivateUserInputDTO, ActivateUserOutputDTO
from usecases.user.activate_user.activate_user_usecase import ActivateUserUseCase
from domain.user.user_entity import User
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_repository_interface import userRepositoryInterface
import pytest
from unittest.mock import MagicMock
from uuid import UUID, uuid4



class TestMockActivateUserUseCase:
	def test_activate_user_usecase_sucess(self):
		# Arrange
		mock_user = MagicMock(spec = userRepositoryInterface)
		mock_hasher = MagicMock(spec=PasswordHasherInterface)

		user_id = uuid4()
		expires_at = datetime.now() + timedelta(minutes=15)
		email_in = "john@example.com"

		mock_user.find_user_by_email.return_value = User(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password="hashed",
            is_active=False,
            activation_code="hashed12345",
            activation_code_expires_at=expires_at,
            roles={"cliente"},
        )
		mock_hasher.verify.return_value = True

		use_case = ActivateUserUseCase(password_hasher=mock_hasher, 
									   user_repository=mock_user)

		input_dto = ActivateUserInputDTO(
			email=email_in,
			activation_code = "abc12345"
		)
		output = use_case.execute(input_dto)


		# Assert
		assert output.id == user_id
		assert output.name == "John Doe"
		assert output.is_active is True
		assert isinstance(output,ActivateUserOutputDTO)

		mock_user.find_user_by_email.assert_called_once_with(email = email_in)
		mock_hasher.verify.assert_called_once_with(password='abc12345', hashed_password='hashed12345')
		mock_user.update_user.assert_called_once()

	def test_activate_user_usecase_usernotfound(self):
		mock_user = MagicMock(spec = userRepositoryInterface)
		mock_hasher = MagicMock(spec=PasswordHasherInterface)
		email_in = "john@example.com"

		mock_user.find_user_by_email.side_effect = UserNotFoundError(email_in)
		use_case = ActivateUserUseCase(password_hasher=mock_hasher, 
									   user_repository=mock_user)

		input_dto = ActivateUserInputDTO(
			email=email_in,
			activation_code = "abc12345"
		)
		with pytest.raises(UserNotFoundError):
			use_case.execute(input_dto)

		mock_user.find_user_by_email.assert_called_once_with(email = email_in)
		mock_hasher.verify.assert_not_called()
		mock_user.update_user.assert_not_called()

		

		




	def test_activate_user_usecase_UserAlreadyActiveError(self):
		# Arrange
		mock_user = MagicMock(spec=userRepositoryInterface)
		mock_hasher = MagicMock(spec=PasswordHasherInterface)

		user_id = uuid4()
		email_in = "john@example.com"

		mock_user.find_user_by_email.return_value = User(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password="hashed",
			is_active=True,  # User is already active
			activation_code="hashed12345",
			activation_code_expires_at=datetime.now() + timedelta(minutes=15),
			roles={"cliente"},
		)
		mock_hasher.verify.return_value = True

		use_case = ActivateUserUseCase(password_hasher=mock_hasher, 
										user_repository=mock_user)

		input_dto = ActivateUserInputDTO(
			email=email_in,
			activation_code="abc12345"
		)

		# Act & Assert
		with pytest.raises(UserAlreadyActiveError):
			use_case.execute(input_dto)

		mock_user.find_user_by_email.assert_called_once_with(email=email_in)
		mock_hasher.verify.assert_not_called()
		mock_user.update_user.assert_not_called()


	def test_activate_user_usecase_code_expires_None(self):
		# Arrange
		mock_user = MagicMock(spec=userRepositoryInterface)
		mock_hasher = MagicMock(spec=PasswordHasherInterface)

		user_id = uuid4()
		email_in = "john@example.com"

		mock_user.find_user_by_email.return_value = User(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password="hashed",
			is_active=False,
			activation_code=None,
			activation_code_expires_at=None,
			roles={"cliente"},
		)
		mock_hasher.verify.return_value = True

		use_case = ActivateUserUseCase(password_hasher=mock_hasher, 
										user_repository=mock_user)

		input_dto = ActivateUserInputDTO(
			email=email_in,
			activation_code="hashed12345"
		)

		with pytest.raises(InvalidActivationCodeError):
			use_case.execute(input_dto)

		mock_user.find_user_by_email.assert_called_once_with(email=email_in)
		mock_hasher.verify.assert_not_called()
		mock_user.update_user.assert_not_called()

	def test_activate_user_usecase_ActivationCodeExpiredError(self):
		# Arrange
		mock_user = MagicMock(spec=userRepositoryInterface)
		mock_hasher = MagicMock(spec=PasswordHasherInterface)

		user_id = uuid4()
		email_in = "john@example.com"

		mock_user.find_user_by_email.return_value = User(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password="hashed",
			is_active=False,
			activation_code="hashed12345",
			activation_code_expires_at=datetime.now() - timedelta(minutes=1),  # Code expired
			roles={"cliente"},
		)
		mock_hasher.verify.return_value = True

		use_case = ActivateUserUseCase(password_hasher=mock_hasher, 
										user_repository=mock_user)

		input_dto = ActivateUserInputDTO(
			email=email_in,
			activation_code="hashed12345"
		)

		# Act & Assert
		with pytest.raises(ActivationCodeExpiredError):
			use_case.execute(input_dto)

		mock_user.find_user_by_email.assert_called_once_with(email=email_in)
		mock_hasher.verify.assert_not_called()
		mock_user.update_user.assert_not_called()

	def test_activate_user_usecase_InvalidActivationCodeError(self):
		# Arrange
		mock_user = MagicMock(spec=userRepositoryInterface)
		mock_hasher = MagicMock(spec=PasswordHasherInterface)

		user_id = uuid4()
		email_in = "john@example.com"

		mock_user.find_user_by_email.return_value = User(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password="hashed",
			is_active=False,
			activation_code="hashed12345",
			activation_code_expires_at=datetime.now() + timedelta(minutes=15),
			roles={"cliente"},
		)
		mock_hasher.verify.return_value = False  # Invalid activation code

		use_case = ActivateUserUseCase(password_hasher=mock_hasher, 
										user_repository=mock_user)

		input_dto = ActivateUserInputDTO(
			email=email_in,
			activation_code="invalid_code"
		)

		# Act & Assert
		with pytest.raises(InvalidActivationCodeError):
			use_case.execute(input_dto)

		mock_user.find_user_by_email.assert_called_once_with(email=email_in)
		mock_hasher.verify.assert_called_once_with( password=  "invalid_code",  hashed_password="hashed12345")
		mock_user.update_user.assert_not_called()

