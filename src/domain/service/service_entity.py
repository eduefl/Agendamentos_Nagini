from typing import Optional
from uuid import UUID


class Service:
    id: UUID
    name: str
    description: Optional[str]

    def __init__(self, id: UUID, name: str, description: Optional[str] = None):
        self.id = id
        self.name = name
        self.description = description
        if self.validate():
            self.name = name.strip().lower()

    def validate(self) -> bool:
        if not isinstance(self.id, UUID):
            raise ValueError("ID must be a valid UUID.")

        if not isinstance(self.name, str):
            raise ValueError("Name must be a string.")
        if not self.name.strip():
            raise ValueError("Name cannot be empty.")
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Description must be a string or None.")

        return True
