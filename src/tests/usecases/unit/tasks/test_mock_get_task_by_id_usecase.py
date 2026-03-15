from unittest.mock import MagicMock
from uuid import uuid4
import pytest
from domain.task.task_exceptions import TaskNotFoundError
from domain.task.task_entity import Task
from usecases.task.get_task_by_id.get_task_by_id_dto import getTaskByIdInputDTO, getTaskByIdOutputDTO
from usecases.task.get_task_by_id.get_task_by_id_usecase import GetTaskByIdUseCase
from domain.task.task_repository_interface import taskRepositoryInterface


class TestMockGetTaskByIdUseCase:
	def test_mock_get_task_by_id_usecase(self):

		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)

		# caso de uso	
		task_id = uuid4()
		task_mock_repository.get_task_by_id.return_value = Task(id=task_id, 
														        user_id=uuid4(), 
																title="Task 1",
																description="Description for Task", 
																completed=False)
		usecase = GetTaskByIdUseCase(task_repository=task_mock_repository)

		input_dto =getTaskByIdInputDTO(id=task_id)

		# output(response)
		output = usecase.execute(input=input_dto)

		# verificações
		assert isinstance(output, getTaskByIdOutputDTO)
		assert output.user_id is not None
		assert output.id == task_id
		assert output.title == "Task 1"
		assert output.description == "Description for Task"
		assert output.completed is False
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)

	def test_mock_get_task_by_id_usecase_task_not_found(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)

		# caso de uso	
		task_id = uuid4()
		task_mock_repository.get_task_by_id.side_effect = TaskNotFoundError(task_id)
		usecase = GetTaskByIdUseCase(task_repository=task_mock_repository)

		input_dto =getTaskByIdInputDTO(id=task_id)

		# output(response)
		# Captura a exceção e valida a mensagem
		with pytest.raises(TaskNotFoundError) as exc_info:
			usecase.execute(input=input_dto)

		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		assert str(exc_info.value) == f'Task with id {task_id} not found'

		

			

		
