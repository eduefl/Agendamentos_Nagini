from pydantic import BaseModel
from uuid import UUID

# input
class UpdateUserInputDTO(BaseModel):
	id: UUID
	name: str
# output
class UpdateUserOutputDTO(BaseModel):
	id: UUID
	name: str