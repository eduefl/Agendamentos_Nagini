from usecases.task.mark_as_completed.mark_as_completed_dto import MarkAsCompletedInputDTO, MarkAsCompletedOutputDTO
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.__seedwork.task_case_interface import TaskCaseInterface


class MarkAsCompletedUseCase(TaskCaseInterface):
	def __init__(self, task_repository: taskRepositoryInterface):
		self.task_repository = task_repository

	def execute(self, input_dto: MarkAsCompletedInputDTO) -> MarkAsCompletedOutputDTO:
		task = self.task_repository.get_task_by_id(input_dto.id)  # Confirma que a tarefa existe, se não existir, o método get_by_id deve lançar uma exceção
		task.mark_as_completed()
		self.task_repository.update_task(task)
		return MarkAsCompletedOutputDTO(id=task.id, 
									 user_id=task.user_id, 
									 title=task.title, 
									 description=task.description, 
									 completed=task.completed
									)