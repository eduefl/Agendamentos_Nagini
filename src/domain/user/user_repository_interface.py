from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from domain.user.user_entity import User


# Metodo: -> INPUT -> OUTPUT
class userRepositoryInterface(ABC):
	@abstractmethod
	def add_user(self, user: User) -> None:
		raise NotImplementedError
	
	@abstractmethod
	def find_user_by_id(self, user_id: UUID ) -> User:
		raise NotImplementedError
	
	@abstractmethod
	def update_user(self, user: User) -> None:
		raise NotImplementedError

	@abstractmethod
	def list_users(self) -> List[User]:
		raise NotImplementedError
	
	
	
	

	

# Nao mudar 