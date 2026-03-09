from pydantic import BaseModel
from uuid import UUID


class DeleteTaskInputDTO(BaseModel):
    id: UUID


class DeleteTaskOutputDTO(BaseModel):
    message: str
