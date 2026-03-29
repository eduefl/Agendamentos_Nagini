from domain.__seedwork.exceptions import  UnauthorizedError
class SecurityError(Exception):
    """Erro base do domínio."""


class SettingsError (SecurityError):
    def __init__(self, message: str = "Settings error"):
        super().__init__(message)


class InvalidTokenError(UnauthorizedError):
    def __init__(self):
        super().__init__("Invalid Token")


class ExpiredTokenError(UnauthorizedError):
    def __init__(self):
        super().__init__("Expired Token")


