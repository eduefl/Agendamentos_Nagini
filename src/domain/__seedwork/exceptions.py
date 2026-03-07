class DomainError(Exception):
    """Erro base do domínio."""


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


class ValidationError(DomainError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message)