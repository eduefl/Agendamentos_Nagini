from pydantic import BaseModel, EmailStr, Field


class AuthenticateUserInputDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)



class AuthenticateUserOutputDTO(BaseModel):
    access_token: str
    token_type: str
