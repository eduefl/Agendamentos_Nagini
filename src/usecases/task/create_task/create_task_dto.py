from uuid import UUID
from pydantic import BaseModel, EmailStr



class CreateTaskInputDTO(BaseModel):
	user_id: UUID
	title: str
	description: str

class createTaskOutputDTO(BaseModel):
	id: UUID
	user_id: UUID
	title: str
	description: str
	completed: bool