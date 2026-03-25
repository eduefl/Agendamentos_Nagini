from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class ActivateUserInputDTO(BaseModel):
    email: EmailStr
    activation_code: str = Field(min_length=1)



class ActivateUserOutputDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: list[str]
