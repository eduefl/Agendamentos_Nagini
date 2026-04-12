"""
ApplyPaymentResultUseCase — Fase 4.

Recebe o resultado da ACL de pagamento e aplica o desfecho ao ServiceRequest
e à PaymentAttempt de forma atômica.

- Aprovado: PAYMENT_PROCESSING -> COMPLETED
- Recusado: PAYMENT_PROCESSING -> AWAITING_PAYMENT (estado anterior para retry)

Notificações são disparadas fora do trecho crítico (best effort).
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.payment.payment_attempt_repository_interface import (
    PaymentAttemptRepositoryInterface,
)
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_dto import PaymentResultDTO
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    PaymentResultStatusInvalidError,
    ServiceRequestAlreadyCompletedError,
    ServiceRequestNotFoundError,
    ServiceRequestPaymentNotProcessingError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)

logger = logging.getLogger(__name__)


class ApplyPaymentResultUseCase:
    """
    Aplica o resultado da ACL de pagamento ao estado persistido de forma atômica.

    Fase 4: aplica desfecho completo (APPROVED -> COMPLETED, REFUSED -> AWAITING_PAYMENT),
    persiste rastreabilidade do gateway, e notifica cliente e prestador fora do
    trecho crítico.
    """

    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        payment_attempt_repository: PaymentAttemptRepositoryInterface,
        notification_gateway: Optional[ServiceRequestNotificationGatewayInterface] = None,
    ):
        self._service_request_repository = service_request_repository
        self._payment_attempt_repository = payment_attempt_repository
        self._notification_gateway = notification_gateway

    def execute(
        self,
        service_request_id: UUID,
        attempt_id: UUID,
        payment_result: PaymentResultDTO,
        now: datetime,
    ) -> None:
        # 1. Validar que o status do resultado é APPROVED ou REFUSED
        self._validate_result_status(payment_result)

        # 2. Determinar timestamp canônico
        processed_at = payment_result.processed_at or now

        # 3. Aplicar desfecho com método atômico
        if payment_result.status == PaymentAttemptStatus.APPROVED:
            self._apply_approved_result(
                service_request_id=service_request_id,
                attempt_id=attempt_id,
                payment_result=payment_result,
                processed_at=processed_at,
            )
        else:
            self._apply_refused_result(
                service_request_id=service_request_id,
                attempt_id=attempt_id,
                payment_result=payment_result,
                processed_at=processed_at,
            )

    def _validate_result_status(self, payment_result: PaymentResultDTO) -> None:
        valid = {PaymentAttemptStatus.APPROVED.value, PaymentAttemptStatus.REFUSED.value}
        status = (
            payment_result.status.value
            if isinstance(payment_result.status, PaymentAttemptStatus)
            else str(payment_result.status)
        )
        if status not in valid:
            raise PaymentResultStatusInvalidError()

    def _apply_approved_result(
        self,
        service_request_id: UUID,
        attempt_id: UUID,
        payment_result: PaymentResultDTO,
        processed_at: datetime,
    ) -> None:
        updated = self._service_request_repository.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=service_request_id,
            attempt_id=attempt_id,
            provider=payment_result.provider,
            external_reference=payment_result.external_reference,
            provider_message=payment_result.provider_message,
            processed_at=processed_at,
        )

        if updated is None:
            self._raise_idempotency_error(service_request_id)

        self._notify_payment_approved(updated, processed_at)

    def _apply_refused_result(
        self,
        service_request_id: UUID,
        attempt_id: UUID,
        payment_result: PaymentResultDTO,
        processed_at: datetime,
    ) -> None:
        updated = self._service_request_repository.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=service_request_id,
            attempt_id=attempt_id,
            provider=payment_result.provider,
            external_reference=payment_result.external_reference,
            refusal_reason=payment_result.refusal_reason,
            provider_message=payment_result.provider_message,
            processed_at=processed_at,
        )

        if updated is None:
            self._raise_idempotency_error(service_request_id)

        self._notify_payment_refused(updated, payment_result.refusal_reason, processed_at)

    def _raise_idempotency_error(self, service_request_id: UUID) -> None:
        """
        Re-lê o ServiceRequest para classificar o erro correto quando o update
        condicional falha (estado inesperado — replay ou concorrência).
        """
        current = self._service_request_repository.find_by_id(service_request_id)
        if current is None:
            raise ServiceRequestNotFoundError()
        if current.status == ServiceRequestStatus.COMPLETED.value:
            raise ServiceRequestAlreadyCompletedError()
        raise ServiceRequestPaymentNotProcessingError()

    def _notify_payment_approved(self, updated, processed_at: datetime) -> None:
        if self._notification_gateway is None:
            return
        try:
            self._notification_gateway.notify_payment_approved(
                client_id=updated.client_id,
                provider_id=updated.accepted_provider_id,
                service_request_id=updated.id,
                payment_amount=updated.payment_amount,
                payment_approved_at=processed_at,
            )
        except Exception:
            logger.exception(
                "Falha ao notificar pagamento aprovado service_request_id=%s. "
                "Transição COMPLETED mantida.",
                updated.id,
            )

    def _notify_payment_refused(self, updated, refusal_reason, processed_at: datetime) -> None:
        if self._notification_gateway is None:
            return
        try:
            self._notification_gateway.notify_payment_refused(
                client_id=updated.client_id,
                provider_id=updated.accepted_provider_id,
                service_request_id=updated.id,
                payment_amount=updated.payment_amount,
                payment_refused_at=processed_at,
                refusal_reason=refusal_reason,
            )
        except Exception:
            logger.exception(
                "Falha ao notificar pagamento recusado service_request_id=%s. "
                "Transição AWAITING_PAYMENT mantida.",
                updated.id,
            )