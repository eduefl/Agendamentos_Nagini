from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.find_user_by_id.find_user_by_id_dto import TaskUsrOutputDTO, findUserByIdOutputDTO, findUserByIdInputDTO
from domain.task.task_repository_interface import taskRepositoryInterface


# crie os metodos init e execute para esse caso de uso de acordo com o padrao do projeto 
class FindUserByIdUseCase(UseCaseInterface):
	def __init__(self, user_repository: userRepositoryInterface, task_repository: taskRepositoryInterface):
		self.user_repository = user_repository
		self.task_repository = task_repository
		

	def execute(self, input: findUserByIdInputDTO) -> findUserByIdOutputDTO:

		user = self.user_repository.find_user_by_id(user_id = input.id)

		tasks_from_user = self.task_repository.list_tasks_from_user(user_id = input.id)
		user.collect_tasks(tasks= tasks_from_user)


		return findUserByIdOutputDTO(id=user.id, 
							   name=user.name, 
							   tasks=[TaskUsrOutputDTO(id=task.id, title=task.title, description=task.description, completed=task.completed) for task in user.tasks], 
							   pending_tasks= user.count_pending_tasks())	