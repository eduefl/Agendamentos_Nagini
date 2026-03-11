from pydantic import BaseModel
from uuid import UUID


class MarkAsCompletedInputDTO(BaseModel):
	id: UUID

class MarkAsCompletedOutputDTO(BaseModel):
	id: UUID
	user_id: UUID
	title: str
	description: str
	completed : bool
	