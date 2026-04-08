from domain.__seedwork.exceptions import (
    ConflictError,
    ForbiddenError,
    ValidationError,
    NotFoundError,
)


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


class ProviderNotAllowedToStartTravelError(ForbiddenError):
    def __init__(self):
        super().__init__("Prestador não é o responsável por esta solicitação")


class ServiceRequestNotConfirmedError(ConflictError):
    def __init__(self):
        super().__init__(
            "Solicitação não está em status CONFIRMED ou não pode iniciar deslocamento"
        )


class ServiceRequestAddressEmptyError(ConflictError):
    def __init__(self):
        super().__init__("Endereço de serviço não pode ser vazio")


class ServiceRequestDepartureAddressEmptyError(ConflictError):
    def __init__(self):
        super().__init__("Endereço de partida não pode ser vazio")


class ServiceRequestExpiredError(ConflictError):
    def __init__(self):
        super().__init__("Solicitação esta expirada")
