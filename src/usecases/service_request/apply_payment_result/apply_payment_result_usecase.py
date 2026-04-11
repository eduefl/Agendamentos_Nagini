"""
ApplyPaymentResultUseCase — Fase 3 (contrato/stub).

Recebe o resultado da ACL de pagamento e aplica o desfecho ao ServiceRequest
e à PaymentAttempt.  A implementação completa fica para a Fase 4 (aprovação e
recusa); aqui a rastreabilidade mínima do gateway é persistida em ambos os
registros.
"""
from datetime import datetime
from uuid import UUID

from domain.payment.payment_attempt_repository_interface import (
    PaymentAttemptRepositoryInterface,
)
from domain.payment.payment_dto import PaymentResultDTO
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)


class ApplyPaymentResultUseCase:
    """
    Aplica o resultado da ACL de pagamento ao estado persistido.

    Fase 3: persiste rastreabilidade mínima do gateway em ServiceRequest e
    PaymentAttempt (external_reference, provider, provider_message).
    A lógica de aprovação/recusa (COMPLETED vs. AWAITING_PAYMENT) será
    implementada na Fase 4.
    """

    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        payment_attempt_repository: PaymentAttemptRepositoryInterface,
    ):
        self._service_request_repository = service_request_repository
        self._payment_attempt_repository = payment_attempt_repository

    def execute(
        self,
        service_request_id: UUID,
        attempt_id: UUID,
        payment_result: PaymentResultDTO,
        now: datetime,
    ) -> None:
        """
        Stub da Fase 3 — persiste rastreabilidade do gateway em ambos os registros.

        A Fase 4 implementará a máquina de estados completa
        (PAYMENT_PROCESSING -> COMPLETED | AWAITING_PAYMENT).
        """
        # Persiste referência e provedor no ServiceRequest
        service_request = self._service_request_repository.find_by_id(
            service_request_id
        )
        if service_request is not None:
            service_request.payment_reference = payment_result.external_reference
            service_request.payment_provider = payment_result.provider
            self._service_request_repository.update(service_request)

        # Persiste referência e provedor na PaymentAttempt (rastreabilidade da integração)
        self._payment_attempt_repository.record_gateway_reference(
            attempt_id=attempt_id,
            provider=payment_result.provider,
            external_reference=payment_result.external_reference,
            provider_message=payment_result.provider_message,
        )