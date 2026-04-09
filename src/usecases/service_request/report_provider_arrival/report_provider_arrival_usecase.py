import logging
from datetime import datetime
from typing import Optional

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderNotAllowedToReportArrivalError,
    ServiceRequestArrivalAlreadyReportedError,
    ServiceRequestNotFoundError,
    ServiceRequestNotInTransitError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.report_provider_arrival.report_provider_arrival_dto import (
    ReportProviderArrivalInputDTO,
    ReportProviderArrivalOutputDTO,
)

logger = logging.getLogger(__name__)


class ReportProviderArrivalUseCase:
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
        input_dto: ReportProviderArrivalInputDTO,
    ) -> ReportProviderArrivalOutputDTO:
        # 1. Buscar ServiceRequest por id
        service_request = self._service_request_repository.find_by_id(
            input_dto.service_request_id
        )
        if service_request is None:
            raise ServiceRequestNotFoundError()

        # 2. Validar que o usuário autenticado é o accepted_provider_id
        if service_request.accepted_provider_id != input_dto.authenticated_user_id:
            raise ProviderNotAllowedToReportArrivalError()

        # 3. Validar que o status é IN_TRANSIT
        if service_request.status != ServiceRequestStatus.IN_TRANSIT.value:
            if service_request.status in (
                ServiceRequestStatus.ARRIVED.value,
                ServiceRequestStatus.IN_PROGRESS.value,
            ):
                raise ServiceRequestArrivalAlreadyReportedError()
            raise ServiceRequestNotInTransitError()

        # 4. Capturar now
        now = datetime.utcnow()

        # 5. Update condicional no repositório: IN_TRANSIT → ARRIVED
        updated = self._service_request_repository.mark_arrived_if_in_transit(
            service_request_id=input_dto.service_request_id,
            provider_id=input_dto.authenticated_user_id,
            now=now,
        )

        if updated is None:
            current = self._service_request_repository.find_by_id(
                input_dto.service_request_id
            )

            if current is None:
                raise ServiceRequestNotFoundError()

            if current.accepted_provider_id != input_dto.authenticated_user_id:
                raise ProviderNotAllowedToReportArrivalError()

            if current.status in (
                ServiceRequestStatus.ARRIVED.value,
                ServiceRequestStatus.IN_PROGRESS.value,
            ):
                raise ServiceRequestArrivalAlreadyReportedError()

            raise ServiceRequestNotInTransitError()

        # 6. Notificar cliente em best effort (fora do trecho crítico)
        if self._notification_gateway is not None:
            try:
                self._notification_gateway.notify_client_provider_arrived(
                    client_id=updated.client_id,
                    service_request_id=updated.id,
                    provider_arrived_at=updated.provider_arrived_at,
                )
            except EmailDeliveryError:
                logger.exception(
                    "Falha ao notificar cliente sobre chegada do prestador "
                    "service_request_id=%s. Transição ARRIVED mantida.",
                    updated.id,
                )

        return ReportProviderArrivalOutputDTO(
            service_request_id=updated.id,
            status=updated.status,
            provider_arrived_at=updated.provider_arrived_at,
        )
