from usecases.task.update_task_dto import UpdateTaskInputDTO, UpdateTaskOutputDTO
from domain.__seedwork.task_case_interface import TaskCaseInterface
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.user.user_repository_interface import userRepositoryInterface


class UpdateTaskUseCase(TaskCaseInterface):
	def __init__(self, task_repository: taskRepositoryInterface,
			  user_repository: userRepositoryInterface):
		self.task_repository = task_repository
		self.user_repository = user_repository

	def execute(self, input_dto: UpdateTaskInputDTO) -> UpdateTaskOutputDTO:
		task = self.task_repository.get_task_by_id(input_dto.id) #Confirmo que a tarefa existe, se não existir, o método get_by_id deve lançar uma exceção
		if input_dto.user_id is not None:
			# só valida existência do usuário, se user_id for fornecido	
			# Caso nao exista o usuario levanta uma exeção, caso exista, o método find_user_by_id pode retornar o usuário ou apenas validar a existência, dependendo da implementação do repositório de usuários
			self.user_repository.find_user_by_id(input_dto.user_id)  
			task.user_id = input_dto.user_id	
		if input_dto.title is not None:
			task.title = input_dto.title
		if input_dto.description is not None:
			task.description = input_dto.description
		if input_dto.completed is not None:
			task.completed = input_dto.completed		
		self.task_repository.update_task(task)
		return UpdateTaskOutputDTO(id=task.id, 
							 user_id=task.user_id, 
							 title=task.title, 
							 description=task.description, 
							 completed=task.completed
							 )	