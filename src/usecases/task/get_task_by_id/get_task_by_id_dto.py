from uuid import UUID
from pydantic import BaseModel, EmailStr



class getTaskByIdInputDTO(BaseModel):
	id: UUID

class getTaskByIdOutputDTO(BaseModel):
	id: UUID
	title: str
	description: str
	user_id: UUID
	completed: bool