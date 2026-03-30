from domain.__seedwork.exceptions import NotFoundError, ConflictError


class ServiceNotFoundError(NotFoundError):
    def __init__(self, value: str, attribute: str = "id"):
        super().__init__(f"Service with {attribute} {value} not found")


class ProviderServiceAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__("This Provider already offers this service")


