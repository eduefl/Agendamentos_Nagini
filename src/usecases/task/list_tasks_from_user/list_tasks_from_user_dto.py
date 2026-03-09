from pydantic import BaseModel
from typing import List
from uuid import UUID

# input

class ListTasksFromUserInputDTO(BaseModel):
	user_id: UUID

# output

class TaskDTO(BaseModel):
	id: UUID
	user_id: UUID
	title: str
	description: str
	completed: bool

class ListTasksFromUserOutputDTO(BaseModel):
	tasks: List[TaskDTO]


