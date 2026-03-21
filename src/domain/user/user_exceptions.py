from uuid import UUID
from domain.__seedwork.exceptions import ForbiddenError, NotFoundError, ConflictError, ValidationError

class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: UUID):
        super().__init__(f"User with id {user_id} not found")
        self.user_id = user_id

class EmailAlreadyExistsError(ConflictError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists")
        self.email = email
class RoleNotFoundError(NotFoundError):
    def __init__(self, role_name: str):
        super().__init__(f"Role {role_name} not found")
        self.role_name = role_name

class RolesRequiredError(ValidationError):
    def __init__(self):
        super().__init__("User roles are required")

class RoleRemovalNotAllowedError(ForbiddenError):
    def __init__(self, role_name: str):
        super().__init__(f"Role removal is not allowed: {role_name}")
        self.role_name = role_name
        
