from unittest.mock import MagicMock
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from usecases.task.create_task.create_task_dto import CreateTaskInputDTO, createTaskOutputDTO
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.task.create_task.create_task_usecase import CreateTaskUseCase
import pytest


class TestMockCreateTaskUseCase:

	def test_mock_create_task_valid(self):
		
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)	
		user_mock_repository = MagicMock(spec=userRepositoryInterface)


		# caso de uso
		use_case = CreateTaskUseCase(task_mock_repository, user_mock_repository)	
		user_id = uuid4()
		input_dto = CreateTaskInputDTO(user_id = user_id , 
								 		title="Task 1", 
										description="Description for Task")
		user_mock_repository.find_user_by_id.return_value = User(id=user_id, name="John Doe")
		
		# output(response)
		output = use_case.execute(input = input_dto)

		# verificações
		assert output.id is not None
		assert output.title == "Task 1"
		assert output.description == "Description for Task"
		assert output.user_id == user_id
		assert output.completed is False
		# assert user_mock_repository.find_user_by_id.called is True
		# assert task_mock_repository.create_task.called is True
		user_mock_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
		task_mock_repository.create_task.assert_called_once()
		args, kwargs = task_mock_repository.create_task.call_args
		created_task = kwargs.get("task") or args[0]

		assert created_task.user_id == user_id
		assert created_task.title == "Task 1"
		assert created_task.description == "Description for Task"
		assert created_task.completed is False
		assert output.id == created_task.id

		assert isinstance(output, createTaskOutputDTO) 



	def test_mock_create_task_user_not_found(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)	
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		use_case = CreateTaskUseCase(task_mock_repository, user_mock_repository)	
		user_id = uuid4()
		user_mock_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

		input_dto = CreateTaskInputDTO(user_id = user_id , 
								 		title="Task 1", 
										description="Description for Task")

		# Act / Assert
		with pytest.raises(UserNotFoundError):
			use_case.execute(input=input_dto)

		user_mock_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
		task_mock_repository.create_task.assert_not_called()
        		





