from domain.user.user_repository_interface import userRepositoryInterface
from usecases.task.list_tasks_from_user.list_tasks_from_user_dto import ListTasksFromUserInputDTO, ListTasksFromUserOutputDTO, TaskDTO
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.__seedwork.use_case_interface import UseCaseInterface


class ListTasksFromUserUseCase(UseCaseInterface):
	def __init__(self, task_repository: taskRepositoryInterface,
			  user_repository: userRepositoryInterface):
		self.task_repository = task_repository
		self.user_repository = user_repository

	def execute(self, input: ListTasksFromUserInputDTO) -> ListTasksFromUserOutputDTO:
		# Verifica se o usuário existe, se não existir, o método find_user_by_id deve lançar uma exceção
		self.user_repository.find_user_by_id(input.user_id) 
		tasks = self.task_repository.list_tasks_from_user(input.user_id)
		tasks_dto = [TaskDTO(id=task.id, 
					   	title=task.title, 
						description=task.description, 
						user_id=task.user_id, 
						completed=task.completed) for task in tasks]	
		return ListTasksFromUserOutputDTO(tasks=tasks_dto)
