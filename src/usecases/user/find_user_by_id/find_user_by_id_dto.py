from uuid import UUID
from pydantic import BaseModel
# Input
class findUserByIdInputDTO(BaseModel):
	id: UUID

# Output
class findUserByIdOutputDTO(BaseModel):
	id: UUID
	name: str