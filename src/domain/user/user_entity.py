from typing import List
from uuid import UUID

from domain.task.task_entity import Task

class User:
	
	id: UUID
	name: str
	tasks: List[Task]

	def __init__(self, id: UUID, name: str):
		self.id = id
		self.name = name
		self.tasks = []
		self.validate()

	def validate(self):
		if not isinstance(self.id, UUID):
			raise ValueError("ID must be a valid UUID.")
		if not isinstance(self.name, str):
			raise ValueError("Name must be a string.")
		if not self.name.strip():
			raise ValueError("Name cannot be empty.")
		
	def collect_tasks(self, tasks: List[Task]) -> None:
		"""
		Adds a list of tasks to the user's task list.

		Parameters:
		tasks (List[Task]): A list of Task objects to be added to the user's tasks.

		Returns:
		None
		"""
		self.tasks.extend(tasks)#extend para adicionar a lista de tarefas ao atributo tasks do usuário eu adiciono todos os itens do parametro ao objeto caller

	def count_pending_tasks(self) -> int:
		"""
		Counts the number of pending tasks.

		Returns:
			int: The total number of tasks that are not completed.
		"""
		return sum(1 for task in self.tasks if not task.completed)
	

	def __str__(self):
		return f"User(id={self.id}, name='{self.name}')"
