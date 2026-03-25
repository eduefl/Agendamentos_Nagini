from abc import ABC, abstractmethod
from typing import List, Set
from uuid import UUID

from domain.user.user_entity import User


# Metodo: -> INPUT -> OUTPUT
class userRepositoryInterface(ABC):
    @abstractmethod
    def add_user(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_user_by_id(self, user_id: UUID) -> User:
        raise NotImplementedError

    @abstractmethod
    def find_user_by_email(self, email: str) -> User:
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_users(self) -> List[User]:
        raise NotImplementedError

    # --- roles ---
    @abstractmethod
    def add_role_to_user(self, user_id: UUID, role_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_role_from_user(self, user_id: UUID, role_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_user_roles(self, user_id: UUID) -> Set[str]:
        raise NotImplementedError