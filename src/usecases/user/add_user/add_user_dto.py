from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# INPUT
class AddUserInputDTO(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(min_length=1)  # ex: "cliente" ou "prestador"


# OUTPUT (nunca retornar hashed_password)
class AddUserOutputDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: list[str]