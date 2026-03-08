from uuid import UUID
from domain.task.task_exceptions import TaskNotFoundError
from domain.task.task_entity import Task
from domain.task.task_repository_interface import taskRepositoryInterface
from sqlalchemy.orm.session import Session
from infrastructure.task.sqlalchemy.task_model import TaskModel

class taskRepository(taskRepositoryInterface):
	
	def __init__(self, session):
		self.session = session

	def create_task(self, task: Task) -> None:
		task_model = TaskModel(
			id=task.id,
			user_id=task.user_id,
			title=task.title,
			description=task.description,
			completed=task.completed
		)
		self.session.add(task_model)
		self.session.commit()
	
	def get_task_by_id(self, task_id: UUID) -> Task:
		task_in_db = self.session.get(TaskModel, task_id)
		if not task_in_db:
			raise TaskNotFoundError(task_id)

		task = Task(id=task_in_db.id, 
					title=task_in_db.title, 
					description=task_in_db.description, 
					user_id=task_in_db.user_id, 
					completed=task_in_db.completed)
		return task

	def update_task(self, task: Task) -> None:
		pass

	def delete_task(self, task_id: UUID) -> str:
		pass
	

