


from unittest.mock import MagicMock
from uuid import uuid4
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.update_user.update_user_dto import UpdateUserInputDTO
from usecases.user.update_user.update_user_usecase import updateUserUsecase
import pytest


class TestMockUpdateUserUseCase:
	def test_Mock_Update_User_UseCase(self):
		mock_user_repository = MagicMock(spec=userRepositoryInterface)

		user_id = uuid4()
		mock_user_repository.find_user_by_id.return_value = User(id=user_id, name="John Doe")

		use_case = updateUserUsecase(mock_user_repository)

		input_dto = UpdateUserInputDTO(id=user_id, name="Jane Doe")
		output = use_case.execute(input_dto)

		assert output.id == user_id
		assert output.name == "Jane Doe"
		mock_user_repository.find_user_by_id.assert_called_once_with( user_id = user_id)
		mock_user_repository.update_user.assert_called_once()
		# args, kwargs = mock_user_repository.update_user.call_args
		args, _ = mock_user_repository.update_user.call_args
		# Como no "Actual" a chamada foi posicional, o User estará em args[0]
		updated_user = args[0]

		assert isinstance(updated_user, User)
		assert updated_user.id == user_id
		assert updated_user.name == "Jane Doe"

	def test_Mock_Update_User_UseCase_User_Not_Found(self):
		mock_user_repository = MagicMock(spec=userRepositoryInterface)

		user_id = uuid4()
		mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

		use_case = updateUserUsecase(mock_user_repository)

		input_dto = UpdateUserInputDTO(id=user_id, name="Jane Doe")

		with pytest.raises(UserNotFoundError):
			use_case.execute(input_dto)

		mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
		mock_user_repository.update_user.assert_not_called()
		# mock_user_repository.update_user.assert_called_once()

