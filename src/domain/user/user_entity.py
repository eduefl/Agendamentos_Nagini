from datetime import datetime
from typing import List, Optional, Set, Iterable
from uuid import UUID

from domain.task.task_entity import Task


class User:
    id: UUID
    name: str
    email: str
    hashed_password: str
    is_active: bool
    activation_code: Optional[str]
    activation_code_expires_at: Optional[datetime]
    roles: Set[str]
    tasks: List[Task]

    def __init__(
        self,
        id: UUID,
        name: str,
        email: str,
        hashed_password: str,
        is_active: bool = False,
        activation_code: Optional[str] = None,
        activation_code_expires_at: Optional[datetime] = None,
        roles: Optional[Iterable[str]] = None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.activation_code = activation_code
        self.activation_code_expires_at = activation_code_expires_at
        self.roles = set(roles) if roles is not None else set()
        self.tasks = []
        self.validate()

    def validate(self) -> bool:
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

        if self.activation_code is not None:
            if not isinstance(self.activation_code, str):
                raise ValueError("Activation code must be a string.")
            if not self.activation_code.strip():
                raise ValueError("Activation code cannot be empty when provided.")

        if self.activation_code_expires_at is not None:
            if not isinstance(self.activation_code_expires_at, datetime):
                raise ValueError("Activation code expiration must be a datetime.")

        if self.activation_code is not None and self.activation_code_expires_at is None:
            raise ValueError(
                "Activation code expiration must be provided when activation code exists."
            )

        if self.activation_code is None and self.activation_code_expires_at is not None:
            raise ValueError("Activation code must be provided when expiration exists.")

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
        self.clear_activation_code()

    def set_activation_code(self, code: str, expires_at: datetime) -> None:
        normalized_code = code.strip()
        if not normalized_code:
            raise ValueError("Activation code must be a non-empty string.")
        if expires_at is None:
            raise ValueError(
                "Activation code expiration must be provided when activation code exists."
            )

        self.activation_code = normalized_code
        self.activation_code_expires_at = expires_at

    def clear_activation_code(self) -> None:
        self.activation_code = None
        self.activation_code_expires_at = None

    def is_provider(self) -> bool:
        return self.has_role("prestador")

    def is_client(self) -> bool:
        return self.has_role("cliente")

    def __str__(self) -> str:
        # não exibir hashed_password
        roles = sorted(self.roles)
        return (
            f"User(id={self.id}, name='{self.name}', email='{self.email}', "
            f"is_active={self.is_active}, roles={roles})"
        )
