from enum import Enum


class PaymentStatusSnapshot(str, Enum):
    """
    Snapshot do último estado de pagamento armazenado no ServiceRequest.

    Representa o ciclo da tentativa de pagamento, separado do ciclo do atendimento
    (ServiceRequestStatus). Usado no campo payment_last_status do ServiceRequest.
    """
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"