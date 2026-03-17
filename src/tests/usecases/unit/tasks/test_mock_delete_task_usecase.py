from unittest.mock import MagicMock
from uuid import uuid4
from domain.task.task_exceptions import TaskNotFoundError
from domain.task.task_repository_interface import taskRepositoryInterface
from usecases.task.delete_task.delete_task_dto import DeleteTaskInputDTO, DeleteTaskOutputDTO
from usecases.task.delete_task.delete_task_usecase import DeleteTaskUseCase
import pytest

class TestMockDeleteTaskUseCase:
	def test_delete_task(self):
		# Arrange
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)

		usecase = DeleteTaskUseCase(task_repository=task_mock_repository)

		task_id = uuid4()
		input_dto = DeleteTaskInputDTO(id=task_id)

		task_mock_repository.delete_task.return_value = None

			

		# Act
		output = usecase.execute(input=input_dto)	
		
		# Assert
		assert isinstance(output, DeleteTaskOutputDTO)
		assert output.message == f"Task with id {task_id} deleted successfully."
		task_mock_repository.delete_task.assert_called_once_with(task_id=task_id)

	def test_delete_nonexistent_task(self):
		# Arrange
		task_mock_repository = MagicMock(spec=taskRepositoryInterface)

		usecase = DeleteTaskUseCase(task_repository=task_mock_repository)

		task_id = uuid4()
		input_dto = DeleteTaskInputDTO(id=task_id)

		task_mock_repository.delete_task.side_effect = TaskNotFoundError(task_id)

		# Act & Assert
		# output(response)
		with pytest.raises(TaskNotFoundError) as exc_info:
			usecase.execute(input = input_dto)

		assert str(exc_info.value) == f'Task with id {task_id} not found'
		task_mock_repository.delete_task.assert_called_once_with(task_id=task_id)
			
