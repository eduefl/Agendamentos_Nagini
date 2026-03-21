from typing import List
from uuid import UUID

from domain.task.task_entity import Task


class User:
    id: UUID
    name: str
    email: str
    hashed_password: str
    is_active: bool
    tasks: List[Task]

    def __init__(
        self,
        id: UUID,
        name: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.tasks = []
        self.validate()

    def validate(self):
        if not isinstance(self.id, UUID):
            raise ValueError("ID must be a valid UUID.")

        if not isinstance(self.name, str):
            raise ValueError("Name must be a string.")
        if not self.name.strip():
            raise ValueError("Name cannot be empty.")

        if not isinstance(self.email, str):
            raise ValueError("Email must be a string.")
        email = self.email.strip()
        if not email:
            raise ValueError("Email cannot be empty.")
        if " " in email:
            raise ValueError("Email cannot contain spaces.")
        if "@" not in email:
            raise ValueError("Email must be valid.")
        self.email = email.lower()  # normaliza

        if not isinstance(self.hashed_password, str):
            raise ValueError("Hashed password must be a string.")
        if not self.hashed_password.strip():
            raise ValueError("Hashed password cannot be empty.")

        if not isinstance(self.is_active, bool):
            raise ValueError("is_active must be a boolean.")

        return True

    def collect_tasks(self, tasks: List[Task]) -> None:
        """
        Adds a list of tasks to the user's task list.
        
        Parameters:
        tasks (List[Task]): A list of Task objects to be added to the user's tasks.
        
        Returns:
        None
        """
        
        self.tasks.extend(tasks)

    def count_pending_tasks(self) -> int:
        """
		Counts the number of pending tasks.

		Returns:
			int: The total number of tasks that are not completed.
		"""

        return sum(1 for task in self.tasks if not task.completed)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def __str__(self) -> str:
        # não exibir hashed_password
        return f"User(id={self.id}, name='{self.name}', email='{self.email}', is_active={self.is_active})"