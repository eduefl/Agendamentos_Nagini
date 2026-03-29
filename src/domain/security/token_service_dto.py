from uuid import UUID
from pydantic import BaseModel, EmailStr

class TokenPayloadDTO(BaseModel):
	sub: UUID
	email: EmailStr
	roles: list[str]
	

class CreateAccessTokenDTO(BaseModel):
    sub: UUID 
    email: EmailStr 
    roles: list[str] = []