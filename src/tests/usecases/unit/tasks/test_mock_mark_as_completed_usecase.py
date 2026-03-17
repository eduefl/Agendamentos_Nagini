from unittest.mock import MagicMock
from uuid import uuid4

from domain.task.task_exceptions import TaskNotFoundError
from domain.task.task_entity import Task
from domain.task.task_repository_interface import taskRepositoryInterface
from usecases.task.mark_as_completed.mark_as_completed_dto import MarkAsCompletedInputDTO, MarkAsCompletedOutputDTO
from usecases.task.mark_as_completed.mark_as_completed_usecase import MarkAsCompletedUseCase
import pytest

class TestMockMarkAsCompletedUseCase:
	def test_mark_as_completed(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)


		# caso de uso
		usecase = MarkAsCompletedUseCase(task_repository=task_mock_repository)	
		task_id = uuid4()

		# input
		input_dto = MarkAsCompletedInputDTO(id=task_id)
		user_id = uuid4()

		# mockando o comportamento do repositório
		task = Task(id=task_id, 
					user_id=user_id, 
					title="Task 1",
					description="Description for Task", 																
					completed=False)
		task_mock_repository.get_task_by_id.return_value = task

		# task_mock_repository.mark_as_completed.return_value = None	

		# executando o caso de uso
		output = usecase.execute(input=input_dto)

		# assertivas
		assert isinstance(output, MarkAsCompletedOutputDTO)
		assert output.id == task_id
		assert output.user_id == user_id
		assert output.title == "Task 1"
		assert output.description == "Description for Task"
		assert output.completed is True
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		task_mock_repository.update_task.assert_called_once()
		args, kwargs = task_mock_repository.update_task.call_args
		updated_task = kwargs.get("task") or args[0]
		assert updated_task is task
		assert updated_task.id == task.id
		assert updated_task.user_id == task.user_id
		assert updated_task.title == "Task 1"
		assert updated_task.description == "Description for Task"		
		assert updated_task.completed is True


	def test_mark_as_completed_nonexistent_task(self):
		# repositorio
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)

		# caso de uso
		usecase = MarkAsCompletedUseCase(task_repository=task_mock_repository)	
		task_id = uuid4()

		# input
		input_dto = MarkAsCompletedInputDTO(id=task_id)

		# mockando o comportamento do repositório
		task_mock_repository.get_task_by_id.side_effect = TaskNotFoundError(task_id)

		# output(response)
		with pytest.raises(TaskNotFoundError) as exc_info:
			usecase.execute(input = input_dto)

		assert str(exc_info.value) == f'Task with id {task_id} not found'
		task_mock_repository.get_task_by_id.assert_called_once_with(task_id=task_id)
		task_mock_repository.update_task.assert_not_called()



		  
		
