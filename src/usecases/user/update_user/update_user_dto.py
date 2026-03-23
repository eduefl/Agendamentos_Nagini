from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# input
class UpdateUserDataDTO(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    # is_active: Optional[bool] = None

    # no futuro: phone, etc.


class UpdateUserInputDTO(UpdateUserDataDTO):
    id: UUID


# output
class UpdateUserOutputDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: list[str]