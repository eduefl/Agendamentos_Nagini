



from abc import ABC, abstractmethod
from uuid import UUID

from domain.task.task_entity import Task


class taskRepositoryInterface(ABC):
	@abstractmethod
	def create_task(self, task : Task) ->None:
		raise NotImplementedError

	@abstractmethod
	def get_task_by_id(self, task_id: UUID) -> Task:
		raise NotImplementedError

	@abstractmethod
	def update_task(self, task: Task) -> None:
		raise NotImplementedError

	def delete_task(self, task_id: UUID) -> str:
		raise NotImplementedError
	
	def list_tasks_from_user(self, user_id: UUID) -> list[Task]:
		raise NotImplementedError
