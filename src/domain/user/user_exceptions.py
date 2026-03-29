from uuid import UUID
from domain.__seedwork.exceptions import ForbiddenError, NotFoundError, ConflictError, UnauthorizedError, ValidationError

class UserNotFoundError(NotFoundError):
    def __init__(self, value: str, attribute: str = "id"):
        super().__init__(f"User with {attribute} {value} not found")
        self.value = value
        self.attribute = attribute

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
        
class ActivationCodeExpiredError(ValidationError):
    def __init__(self):
        super().__init__("Activation code has expired")


class InvalidActivationCodeError(ValidationError):
    def __init__(self):
        super().__init__("Invalid activation code")


class UserAlreadyActiveError(ConflictError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} is already active")
        self.email = email

class InvalidCredentialsError(UnauthorizedError):
    def __init__(self):
        super().__init__("Invalid email or password")

