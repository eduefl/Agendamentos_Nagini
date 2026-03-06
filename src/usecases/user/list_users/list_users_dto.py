from pydantic import BaseModel
# from domain.user import User	
from typing import List
from uuid import UUID
# input

class ListUsersInputDTO(BaseModel):
	pass

class UserDto(BaseModel):
	id: UUID
	name: str

# output

class ListUsersOutputDTO(BaseModel):
	users: List[UserDto]
