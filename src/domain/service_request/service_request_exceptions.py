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


class ClientNotAllowedToConfirmPaymentError(ForbiddenError):
    def __init__(self):
        super().__init__("Cliente não é o dono desta solicitação de serviço")


class ServiceRequestNotAwaitingPaymentError(ConflictError):
    def __init__(self):
        super().__init__(
            "Solicitação não está em status AWAITING_PAYMENT ou não pode confirmar pagamento"
        )


class ServiceRequestPaymentAlreadyProcessingError(ConflictError):
    def __init__(self):
        super().__init__("Pagamento já está em processamento para esta solicitação")


class ServiceRequestPaymentNotRequestedError(ConflictError):
    def __init__(self):
        super().__init__(
            "Tentativa de pagamento não encontrada ou não está em status REQUESTED"
        )


class ServiceRequestPaymentAmountInvalidError(ConflictError):
    def __init__(self):
        super().__init__("Valor de pagamento não está definido ou é inválido para esta solicitação")


class ServiceRequestAlreadyCompletedError(ConflictError):
    def __init__(self):
        super().__init__("Solicitação de serviço já foi concluída")


class ServiceRequestPaymentNotProcessingError(ConflictError):
    def __init__(self):
        super().__init__(
            "Solicitação não está em status PAYMENT_PROCESSING ou desfecho já foi aplicado"
        )


class PaymentAttemptNotProcessingError(ConflictError):
    def __init__(self):
        super().__init__(
            "Tentativa de pagamento não está em status PROCESSING ou desfecho já foi aplicado"
        )


class PaymentResultStatusInvalidError(ValidationError):
    def __init__(self):
        super().__init__(
            "Status do resultado de pagamento inválido: deve ser APPROVED ou REFUSED"
        )


class PaymentGatewayTechnicalFailureError(ConflictError):
    """
    Falha técnica do gateway de pagamento antes de devolver resultado.
    O ServiceRequest permanece em PAYMENT_PROCESSING; nenhum desfecho foi aplicado.
    Mapeado para 502/503 na camada HTTP.
    """
    def __init__(self, message: str = "Falha técnica do gateway de pagamento"):
        super().__init__(message)   