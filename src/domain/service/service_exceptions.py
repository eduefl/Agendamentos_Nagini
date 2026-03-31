from domain.__seedwork.exceptions import NotFoundError, ConflictError


class ServiceNotFoundError(NotFoundError):
    def __init__(self, value: str, attribute: str = "id"):
        super().__init__(f"Service with {attribute} {value} not found")


class ProviderServiceAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__("This Provider already offers this service")


class ProviderServiceNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Provider service not found")


class ProviderServiceAlreadyInactiveError(ConflictError):
    def __init__(self):
        super().__init__("This provider service is already inactive")

class ProviderServiceAlreadyActive(ConflictError):
    def __init__(self):
        super().__init__("This provider service is already active")
