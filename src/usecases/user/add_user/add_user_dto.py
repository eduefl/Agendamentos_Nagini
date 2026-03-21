from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# INPUT
class AddUserInputDTO(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)


# OUTPUT (nunca retornar hashed_password)
class AddUserOutputDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool