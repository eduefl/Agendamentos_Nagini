from uuid import UUID
from domain.__seedwork.exceptions import NotFoundError, ValidationError

class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: UUID):
        super().__init__(f"User with id {user_id} not found")
        self.user_id = user_id

class EmailAlreadyExistsError(ValidationError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists")
        self.email = email