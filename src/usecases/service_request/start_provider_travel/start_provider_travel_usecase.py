import logging
from datetime import datetime
from typing import Optional

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.logistics.logistics_acl_gateway_interface import (
    LogisticsAclGatewayInterface,
)
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderNotAllowedToStartTravelError,
    ServiceRequestAddressEmptyError,
    ServiceRequestDepartureAddressEmptyError,
    ServiceRequestExpiredError,
    ServiceRequestNotConfirmedError,
    ServiceRequestNotFoundError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.start_provider_travel.start_provider_travel_dto import (
    StartProviderTravelInputDTO,
    StartProviderTravelOutputDTO,
)

logger = logging.getLogger(__name__)


class StartProviderTravelUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        logistics_acl_gateway: LogisticsAclGatewayInterface,
        notification_gateway: Optional[
            ServiceRequestNotificationGatewayInterface
        ] = None,
    ):
        self._service_request_repository = service_request_repository
        self._logistics_acl_gateway = logistics_acl_gateway
        self._notification_gateway = notification_gateway

    def execute(
        self,
        input_dto: StartProviderTravelInputDTO,
    ) -> StartProviderTravelOutputDTO:
        # 1. Buscar ServiceRequest por id
        service_request = self._service_request_repository.find_by_id(
            input_dto.service_request_id
        )
        if service_request is None:
            raise ServiceRequestNotFoundError()

        # 2. Validar que o usuário autenticado é o accepted_provider_id
        if service_request.accepted_provider_id != input_dto.authenticated_user_id:
            raise ProviderNotAllowedToStartTravelError()

        # 3. Validar que o status é CONFIRMED
        if service_request.status != ServiceRequestStatus.CONFIRMED.value:
            raise ServiceRequestNotConfirmedError()

        # 4. Validar que não está expirado
        now = datetime.utcnow()
        if service_request.expires_at is not None and service_request.expires_at <= now:
            raise ServiceRequestExpiredError()

        # 5. Validar que departure_address existe
        if not service_request.departure_address:
            raise ServiceRequestDepartureAddressEmptyError()
        # 5.1 Validar que request.address
        if not service_request.address:
            raise ServiceRequestAddressEmptyError()

        # 6. Chamar ACL logística mockada
        route_estimate = self._logistics_acl_gateway.estimate_route(
            origin_address=service_request.departure_address,
            destination_address=service_request.address,
            departure_at=now,
        )

        # 7. Update condicional no repositório: CONFIRMED → IN_TRANSIT
        updated = self._service_request_repository.start_travel_if_confirmed(
            service_request_id=input_dto.service_request_id,
            provider_id=input_dto.authenticated_user_id,
            now=now,
            estimated_arrival_at=route_estimate.estimated_arrival_at,
            travel_duration_minutes=route_estimate.duration_minutes,
            travel_distance_km=route_estimate.distance_km,
            logistics_reference=route_estimate.reference,
        )


        if updated is None:
            current = self._service_request_repository.find_by_id(input_dto.service_request_id)

            if current is None:
                raise ServiceRequestNotFoundError()

            if current.accepted_provider_id != input_dto.authenticated_user_id:
                raise ProviderNotAllowedToStartTravelError()

            if current.expires_at is not None and current.expires_at <= now:
                raise ServiceRequestExpiredError()

            raise ServiceRequestNotConfirmedError()

        # 8. Notificar cliente em best effort (fora do trecho crítico)
        if self._notification_gateway is not None:
            try:
                self._notification_gateway.notify_client_travel_started(
                    client_id=updated.client_id,
                    service_request_id=updated.id,
                    estimated_arrival_at=updated.estimated_arrival_at,
                    travel_duration_minutes=updated.travel_duration_minutes,
                )
            except EmailDeliveryError:
                logger.exception(
                    "Falha ao notificar cliente sobre início do deslocamento "
                    "service_request_id=%s. Transição IN_TRANSIT mantida.",
                    updated.id,
                )

        return StartProviderTravelOutputDTO(
            service_request_id=updated.id,
            status=updated.status,
            travel_started_at=updated.travel_started_at,
            estimated_arrival_at=updated.estimated_arrival_at,
            travel_duration_minutes=updated.travel_duration_minutes,
            travel_distance_km=updated.travel_distance_km,
        )
