from uuid import UUID
from pydantic import BaseModel, EmailStr

# INPUT

class AddUserInputDTO(BaseModel):
	name: str

# OUTPUT
class AddUserOutputDTO(BaseModel):
	id: UUID
	name: str
	

