from usecases.task.get_task_by_id_dto import getTaskByIdInputDTO, getTaskByIdOutputDTO
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.__seedwork.use_case_interface import UseCaseInterface


class GetTaskByIdUseCase(UseCaseInterface):
	def __init__(self, task_repository: taskRepositoryInterface):
		self.task_repository = task_repository

	def execute(self, input: getTaskByIdInputDTO) -> getTaskByIdOutputDTO:
		task = self.task_repository.get_task_by_id(task_id = input.id)
		return getTaskByIdOutputDTO(id=task.id, 
							  title=task.title, 
							  description=task.description, 
							  user_id=task.user_id, 
							  completed=task.completed)