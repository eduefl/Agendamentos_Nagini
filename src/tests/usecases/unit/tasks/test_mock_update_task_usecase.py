from unittest.mock import MagicMock
from uuid import uuid4
from domain.user.user_entity import User
from domain.task.task_entity import Task
from domain.user.user_exceptions import UserNotFoundError
from domain.task.task_exceptions import TaskNotFoundError
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.task.update_task.update_task_dto import UpdateTaskInputDTO, UpdateTaskOutputDTO
from usecases.task.update_task.update_task_usecase import UpdateTaskUseCase
import pytest

class TestMockUpdateTaskUseCase:
	def test_mock_update_task_usecase(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		user_id2 = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									   user_id=user_id2,
									   title="Updated Task 1",
									   description="Updated Description for Task")
		
		task_mock_repository.get_task_by_id.return_value = Task(id=task_id, 
																	user_id=uuid4(), 
																	title="Task 1",
																	description="Description for Task", 																
																	completed=False)
		user_mock_repository.find_user_by_id.return_value = User(
															id=user_id2,
															name="Jane Doe",
															email="jane@example.com",
															hashed_password="hashed",
															is_active=True,
														)		

		# output(response)
		output = usecase.execute(input = input_dto)

		# verificações

		assert isinstance(output, UpdateTaskOutputDTO)
		assert output.id == task_id
		assert output.user_id == user_id2
		assert output.title == "Updated Task 1"
		assert output.description == "Updated Description for Task"
		assert output.completed is False
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_called_once_with(user_id=user_id2)
		task_mock_repository.update_task.assert_called_once()
		args, kwargs = task_mock_repository.update_task.call_args
		updated_task = kwargs.get("task") or args[0]
		assert updated_task.id == task_id
		assert updated_task.user_id == user_id2  # se mudou
		assert updated_task.title == "Updated Task 1"
		assert updated_task.description == "Updated Description for Task"
		assert updated_task.completed is False


	def test_mock_update_task_usecase_task_not_found(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									   title="Updated Task 1",
									   description="Updated Description for Task")
		
		task_mock_repository.get_task_by_id.side_effect = TaskNotFoundError(task_id)


		# output(response)
		with pytest.raises(TaskNotFoundError) as exc_info:
			usecase.execute(input = input_dto)

		assert str(exc_info.value) == f'Task with id {task_id} not found'
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_not_called()
		task_mock_repository.update_task.assert_not_called()

	def test_mock_update_task_usecase_user_not_found(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		user_id2 = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									   user_id=user_id2,
									   title="Updated Task 1",
									   description="Updated Description for Task")
		
		task_mock_repository.get_task_by_id.return_value = Task(
			id=task_id,
			user_id=uuid4(),
			title="Task 1",
			description="Description for Task",
			completed=False,
		)		
		
		user_mock_repository.find_user_by_id.side_effect = UserNotFoundError(user_id2)

		# output(response)
		with pytest.raises(UserNotFoundError) as exc_info:
			usecase.execute(input = input_dto)

		assert str(exc_info.value) == f'User with id {user_id2} not found'
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_called_once_with(user_id=user_id2)
		task_mock_repository.update_task.assert_not_called()	

	def test_mock_update_task_usecase_partial_update(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									   title="Partially Updated Task 1")
		
		task_mock_repository.get_task_by_id.return_value = Task(id=task_id, 
																	user_id=uuid4(), 
																	title="Task 1",
																	description="Description for Task", 																
																	completed=False)

		# output(response)
		output = usecase.execute(input = input_dto)

		# verificações

		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_not_called()  # Não deve chamar a validação do usuário, pois user_id não foi fornecido no input_dto
		task_mock_repository.update_task.assert_called_once()
		assert isinstance(output, UpdateTaskOutputDTO)
		assert output.id == task_id
		assert output.title == "Partially Updated Task 1"
		assert output.description == "Description for Task"	
		assert output.completed is False

		args, kwargs = task_mock_repository.update_task.call_args
		updated_task = kwargs.get("task") or args[0]
		assert updated_task.id == task_id
		assert updated_task.title == "Partially Updated Task 1"
		assert updated_task.description == "Description for Task"	
		assert updated_task.completed is False	

		
	def test_mock_update_task_usecase_partial_update_notUser(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		user_id1 = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									title="Updated Task 1",
									description="Updated Description for Task not updated user")
		
		task_mock_repository.get_task_by_id.return_value = Task(id=task_id, 
																	user_id=user_id1, 
																	title="Task 1",
																	description="Description for Task", 																
																	completed=False)

		# output(response)
		output = usecase.execute(input = input_dto)

		# verificações

		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_not_called()  # Não deve chamar a validação do usuário, pois user_id não foi fornecido no input_dto
		task_mock_repository.update_task.assert_called_once()
		assert isinstance(output, UpdateTaskOutputDTO)
		assert output.id == task_id
		assert output.user_id == user_id1
		assert output.title == "Updated Task 1"
		assert output.description == "Updated Description for Task not updated user"	
		assert output.completed is False

		args, kwargs = task_mock_repository.update_task.call_args
		updated_task = kwargs.get("task") or args[0]
		assert updated_task.id == task_id
		assert updated_task.title == "Updated Task 1"
		assert updated_task.description == "Updated Description for Task not updated user"	
		assert updated_task.completed is False	

	def test_mock_update_task_usecase_partial_update_notTitle(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		user_id2 = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									   user_id=user_id2,
									   description="Updated Description for Task not updated title")
		
		task_mock_repository.get_task_by_id.return_value = Task(id=task_id, 
																	user_id=uuid4(), 
																	title="Task 1",
																	description="Description for Task", 																
																	completed=False)

		# output(response)
		output = usecase.execute(input = input_dto)

		# verificações

		assert isinstance(output, UpdateTaskOutputDTO)
		assert output.id == task_id
		assert output.title == "Task 1"
		assert output.user_id == user_id2
		assert output.description == "Updated Description for Task not updated title"	
		assert output.completed is False
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_called_once_with(user_id=user_id2)
		task_mock_repository.update_task.assert_called_once()

		args, kwargs = task_mock_repository.update_task.call_args
		updated_task = kwargs.get("task") or args[0]
		assert updated_task.id == task_id
		assert updated_task.user_id == user_id2  # se mudou
		assert updated_task.title == "Task 1"
		assert updated_task.description == "Updated Description for Task not updated title"	
		assert updated_task.completed is False	

	def test_mock_update_task_usecase_partial_update_notDescription(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)
		user_mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		usecase = UpdateTaskUseCase(task_repository=task_mock_repository, user_repository=user_mock_repository)				
		task_id = uuid4()
		user_id2 = uuid4()
		
		input_dto = UpdateTaskInputDTO(id=task_id,
									user_id=user_id2,
									title="Updated Task 1")
		
		task_mock_repository.get_task_by_id.return_value = Task(id=task_id, 
																	user_id=uuid4(), 
																	title="Task 1",
																	description="Description for Task", 																
																	completed=False)

		# output(response)
		output = usecase.execute(input = input_dto)

		# verificações

		assert isinstance(output, UpdateTaskOutputDTO)
		assert output.id == task_id
		assert output.user_id == user_id2
		assert output.title == "Updated Task 1"
		assert output.description == "Description for Task"
		assert output.completed is False

		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		user_mock_repository.find_user_by_id.assert_called_once_with(user_id=user_id2)
		task_mock_repository.update_task.assert_called_once()
		args, kwargs = task_mock_repository.update_task.call_args
		updated_task = kwargs.get("task") or args[0]
		assert updated_task.id == task_id
		assert updated_task.user_id == user_id2  # se mudou
		assert updated_task.title == "Updated Task 1"
		assert updated_task.description == "Description for Task"
		assert updated_task.completed is False

