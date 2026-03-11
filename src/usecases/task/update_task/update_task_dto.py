from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class UpdateTaskDataDTO(BaseModel):
    user_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None

class UpdateTaskInputDTO(UpdateTaskDataDTO):
	id: UUID

class UpdateTaskOutputDTO(BaseModel):
	id: UUID
	user_id: UUID
	title: str
	description: str
	completed : bool