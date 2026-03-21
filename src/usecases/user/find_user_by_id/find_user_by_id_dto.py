from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


# Input
class findUserByIdInputDTO(BaseModel):
    id: UUID


class TaskUsrOutputDTO(BaseModel):
    id: UUID
    title: str
    description: str
    completed: bool


# Output
class findUserByIdOutputDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: List[str]
    tasks: List[TaskUsrOutputDTO]
    pending_tasks: int