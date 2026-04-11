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



class ProviderNotAllowedToReportArrivalError(ForbiddenError):
    def __init__(self):
        super().__init__("Prestador não é o responsável por esta solicitação")


class ServiceRequestNotInTransitError(ConflictError):
    def __init__(self):
        super().__init__(
            "Solicitação não está em status IN_TRANSIT ou não pode registrar chegada"
        )


class ServiceRequestArrivalAlreadyReportedError(ConflictError):
    def __init__(self):
        super().__init__("Chegada já foi registrada para esta solicitação")

class ClientNotAllowedToConfirmProviderArrivalError(ForbiddenError):
    def __init__(self):
        super().__init__("Cliente não é o dono desta solicitação")
class ServiceRequestNotArrivedError(ConflictError):
    def __init__(self):
        super().__init__(
            "Solicitação não está em status ARRIVED ou não pode confirmar chegada do prestador"
        )
class ServiceRequestProviderArrivalNotRegisteredError(ConflictError):
    def __init__(self):
        super().__init__("Chegada do prestador ainda não foi registrada nesta solicitação")
class ServiceRequestArrivalAlreadyConfirmedError(ConflictError):
    def __init__(self):
        super().__init__("Chegada do prestador já foi confirmada e o serviço está em andamento")

class ProviderNotAllowedToFinishServiceError(ForbiddenError):
    def __init__(self):
        super().__init__("Prestador não é o responsável por esta solicitação")


class ServiceRequestNotInProgressError(ConflictError):
    def __init__(self):
        super().__init__(
            "Solicitação não está em status IN_PROGRESS ou não pode ser finalizada"
        )


class ServiceRequestAlreadyFinishedError(ConflictError):
    def __init__(self):
        super().__init__("Serviço já foi finalizado para esta solicitação")


class ServiceRequestInvalidFinalAmountError(ConflictError):
    def __init__(self):
        super().__init__("Valor final do atendimento não está definido ou é inválido")   