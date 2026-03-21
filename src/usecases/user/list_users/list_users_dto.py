from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


# input
class ListUsersInputDTO(BaseModel):
    pass


class UserDto(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: List[str]


# output
class ListUsersOutputDTO(BaseModel):
    users: List[UserDto]