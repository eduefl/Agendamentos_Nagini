from domain.__seedwork.exceptions import ValidationError, NotFoundError, ConflictError


class InvalidServiceRequestDateError(ValidationError):
    def __init__(self):
        super().__init__("Desired datetime must be in the future")


class ServiceRequestNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Service request not found")


class ServiceRequestUnavailableError(ConflictError):
    def __init__(self):
        super().__init__("Solicitação não está mais disponível para aceite")


class ProviderDoesNotServeThisRequestError(ValidationError):
    def __init__(self):
        super().__init__("Prestador não atende o serviço solicitado")
