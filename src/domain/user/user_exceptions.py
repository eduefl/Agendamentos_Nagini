from uuid import UUID
from domain.__seedwork.exceptions import NotFoundError

class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: UUID):
        super().__init__(f"User with id {user_id} not found")
        self.user_id = user_id