from typing import List, Optional, Set, Iterable
from uuid import UUID

from domain.task.task_entity import Task


class User:
    id: UUID
    name: str
    email: str
    hashed_password: str
    is_active: bool
    roles: Set[str]
    tasks: List[Task]

    def __init__(
        self,
        id: UUID,
        name: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        roles: Optional[Iterable[str]] = None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.roles = set(roles) if roles is not None else set()
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

        # roles validation (aberto para novos tipos)
        if not isinstance(self.roles, set):
            raise ValueError("roles must be a set of strings.")

        normalized_roles: Set[str] = set()
        for role in self.roles:
            if not isinstance(role, str):
                raise ValueError("Each role must be a string.")
            r = role.strip().lower()
            if not r:
                raise ValueError("Role cannot be empty.")
            if " " in r:
                raise ValueError("Role cannot contain spaces.")
            normalized_roles.add(r)

        self.roles = normalized_roles

        return True

    # --- roles helpers ---
    def add_role(self, role: str) -> None:
        r = role.strip().lower()
        if not r:
            raise ValueError("Role cannot be empty.")
        if " " in r:
            raise ValueError("Role cannot contain spaces.")
        self.roles.add(r)

    def remove_role(self, role: str) -> None:
        r = role.strip().lower()
        self.roles.discard(r)

    def has_role(self, role: str) -> bool:
        return role.strip().lower() in self.roles

    # --- tasks ---
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

    # --- state ---
    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def __str__(self) -> str:
        # não exibir hashed_password
        roles = sorted(self.roles)
        return (
            f"User(id={self.id}, name='{self.name}', email='{self.email}', "
            f"is_active={self.is_active}, roles={roles})"
        )