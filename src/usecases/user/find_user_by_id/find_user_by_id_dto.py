from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


# Input
class findUserByIdInputDTO(BaseModel):
    id: UUID



# Output
class findUserByIdOutputDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: List[str]
