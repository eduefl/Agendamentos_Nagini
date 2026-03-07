


from uuid import uuid4
from domain.task.task_entity import Task
from usecases.task.create_task_dto import CreateTaskIpnutDTO, createTaskOutputDTO
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.__seedwork.task_case_interface import TaskCaseInterface


class CreateTaskUseCase(TaskCaseInterface):
	def __init__(self, task_repository: taskRepositoryInterface):
		self.task_repository = task_repository

	def execute(self, input: CreateTaskIpnutDTO) -> createTaskOutputDTO:
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
