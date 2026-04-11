import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderNotAllowedToFinishServiceError,
    ServiceRequestAlreadyFinishedError,
    ServiceRequestInvalidFinalAmountError,
    ServiceRequestNotFoundError,
    ServiceRequestNotInProgressError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.finish_service_and_request_payment.finish_service_and_request_payment_dto import (
    FinishServiceAndRequestPaymentInputDTO,
    FinishServiceAndRequestPaymentOutputDTO,
)

logger = logging.getLogger(__name__)

_ALREADY_FINISHED_STATUSES = {
    ServiceRequestStatus.AWAITING_PAYMENT.value,
    ServiceRequestStatus.PAYMENT_PROCESSING.value,
    ServiceRequestStatus.COMPLETED.value,
}


class FinishServiceAndRequestPaymentUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        notification_gateway: Optional[
            ServiceRequestNotificationGatewayInterface
        ] = None,
    ):
        self._service_request_repository = service_request_repository
        self._notification_gateway = notification_gateway

    def execute(
        self,
        input_dto: FinishServiceAndRequestPaymentInputDTO,
    ) -> FinishServiceAndRequestPaymentOutputDTO:
        # 1. Carregar o ServiceRequest
        service_request = self._service_request_repository.find_by_id(
            input_dto.service_request_id
        )
        if service_request is None:
            raise ServiceRequestNotFoundError()

        # 2. Validar autorização: o usuário autenticado deve ser o accepted_provider_id
        self._validate_actor(service_request, input_dto.authenticated_user_id)

        # 3. Validar status IN_PROGRESS
        self._validate_status(service_request)

        # 4. Validar que service_finished_at não foi preenchido
        if service_request.service_finished_at is not None:
            raise ServiceRequestAlreadyFinishedError()

        # 5. Validar e materializar payment_amount a partir de total_price
        payment_amount = self._resolve_payment_amount(service_request)

        # 6. Capturar timestamp
        now = datetime.utcnow()

        # 7. Gerar ID da PaymentAttempt antes da transação
        payment_attempt_id = uuid4()

        # 8. Persistir transição atômica: ServiceRequest + PaymentAttempt em uma única transação
        updated = self._service_request_repository.finish_service_and_open_payment_if_in_progress(
            service_request_id=input_dto.service_request_id,
            provider_id=input_dto.authenticated_user_id,
            now=now,
            payment_amount=payment_amount,
            payment_attempt_id=payment_attempt_id,
        )

        if updated is None:
            # Update condicional falhou — re-ler para classificar o erro corretamente
            current = self._service_request_repository.find_by_id(
                input_dto.service_request_id
            )
            if current is None:
                raise ServiceRequestNotFoundError()

            if current.accepted_provider_id != input_dto.authenticated_user_id:
                raise ProviderNotAllowedToFinishServiceError()

            if current.status in _ALREADY_FINISHED_STATUSES:
                raise ServiceRequestAlreadyFinishedError()

            raise ServiceRequestNotInProgressError()

        # 9. Notificar cliente em best effort (fora do trecho crítico)
        self._notify_client_best_effort(updated)

        return FinishServiceAndRequestPaymentOutputDTO(
            service_request_id=updated.id,
            status=updated.status,
            service_finished_at=updated.service_finished_at,
            payment_requested_at=updated.payment_requested_at,
            payment_amount=updated.payment_amount,
            payment_last_status=updated.payment_last_status,
        )

    def _validate_actor(self, service_request, authenticated_user_id) -> None:
        if service_request.accepted_provider_id != authenticated_user_id:
            raise ProviderNotAllowedToFinishServiceError()

    def _validate_status(self, service_request) -> None:
        if service_request.status in _ALREADY_FINISHED_STATUSES:
            raise ServiceRequestAlreadyFinishedError()

        if service_request.status != ServiceRequestStatus.IN_PROGRESS.value:
            raise ServiceRequestNotInProgressError()

    def _resolve_payment_amount(self, service_request):
        if service_request.payment_amount is not None and service_request.payment_amount > 0:
            return service_request.payment_amount

        if service_request.total_price is None or service_request.total_price <= 0:
            raise ServiceRequestInvalidFinalAmountError()

        return service_request.total_price

    def _notify_client_best_effort(self, updated) -> None:
        if self._notification_gateway is None:
            return
        try:
            self._notification_gateway.notify_payment_requested(
                client_id=updated.client_id,
                service_request_id=updated.id,
                payment_amount=updated.payment_amount,
                payment_requested_at=updated.payment_requested_at,
            )
        except Exception:
            logger.exception(
                "Falha ao notificar cliente sobre cobrança do serviço "
                "service_request_id=%s. Transição AWAITING_PAYMENT mantida.",
                updated.id,
            )