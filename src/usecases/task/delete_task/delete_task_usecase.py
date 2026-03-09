from domain.task.task_repository_interface import taskRepositoryInterface
from domain.__seedwork.use_case_interface import UseCaseInterface
from usecases.task.delete_task.delete_task_dto import DeleteTaskInputDTO, DeleteTaskOutputDTO


class DeleteTaskUseCase(UseCaseInterface):
	
	def __init__(self, task_repository: taskRepositoryInterface):
		self.task_repository = task_repository

	def execute(self, input: DeleteTaskInputDTO) -> DeleteTaskOutputDTO:
		self.task_repository.delete_task(task_id=input.id)

		return DeleteTaskOutputDTO(
			message=f"Task with id {input.id} deleted successfully."
		)

	