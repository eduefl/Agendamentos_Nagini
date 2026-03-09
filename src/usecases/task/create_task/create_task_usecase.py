


from uuid import uuid4
from domain.user.user_repository_interface import userRepositoryInterface
from domain.task.task_entity import Task
from usecases.task.create_task.create_task_dto import CreateTaskInputDTO, createTaskOutputDTO
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.__seedwork.task_case_interface import TaskCaseInterface


class CreateTaskUseCase(TaskCaseInterface):
	def __init__(self, task_repository: taskRepositoryInterface, 
			  user_repository: userRepositoryInterface):
		self.task_repository = task_repository
		self.user_repository = user_repository	

	def execute(self, input: CreateTaskInputDTO) -> createTaskOutputDTO:
		self.user_repository.find_user_by_id(input.user_id)  # só valida existência
		task = Task(
			id=uuid4(),
			user_id=input.user_id,
			title=input.title,
			description=input.description,
			completed=False
		)
		self.task_repository.create_task(task = task)

		return createTaskOutputDTO(
			id=task.id,
			title=task.title,
			description=input.description,
			user_id=task.user_id,
			completed=task.completed
		)	
