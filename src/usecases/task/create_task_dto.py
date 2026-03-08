from uuid import UUID
from pydantic import BaseModel, EmailStr



class CreateTaskInputDTO(BaseModel):
	title: str
	description: str
	user_id: UUID

class createTaskOutputDTO(BaseModel):
	id: UUID
	title: str
	description: str
	user_id: UUID
	completed: bool