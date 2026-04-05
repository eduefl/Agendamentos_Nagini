from datetime import datetime
from typing import Optional

from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ServiceRequestNotFoundError,
    ServiceRequestUnavailableError,
    ProviderDoesNotServeThisRequestError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.travel.travel_price_gateway_interface import TravelPriceGatewayInterface
from usecases.service_request.confirm_service_request.confirm_service_request_dto import (
    ConfirmServiceRequestInputDTO,
    ConfirmServiceRequestOutputDTO,
)


class ConfirmServiceRequestUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        provider_service_repository: ProviderServiceRepositoryInterface,
        travel_price_gateway: TravelPriceGatewayInterface,
        notification_service=None,
    ):
        self._service_request_repository = service_request_repository
        self._provider_service_repository = provider_service_repository
        self._travel_price_gateway = travel_price_gateway
        self._notification_service = notification_service

    def execute(
        self,
        input_dto: ConfirmServiceRequestInputDTO,
    ) -> ConfirmServiceRequestOutputDTO:
        # Etapa 1 — carregar a request
        service_request = self._service_request_repository.find_by_id(
            input_dto.service_request_id
        )
        if service_request is None:
            raise ServiceRequestNotFoundError()

        # Etapa 2 — validar disponibilidade lógica
        now = datetime.utcnow()
        is_wrong_status = service_request.status != ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        is_expired = service_request.expires_at is not None and service_request.expires_at <= now

        if is_wrong_status or is_expired:
            raise ServiceRequestUnavailableError()

        # Etapa 3 — validar elegibilidade do prestador
        provider_service = self._provider_service_repository.find_active_by_provider_and_service(
            provider_id=input_dto.provider_id,
            service_id=service_request.service_id,
        )
        if provider_service is None:
            raise ProviderDoesNotServeThisRequestError()

        # Etapa 4 — capturar dados para precificação
        service_price = provider_service.price
        travel_price = self._travel_price_gateway.calculate_price(
            departure_address=input_dto.departure_address,
            destination_address=service_request.address or "",
        )
        total_price = service_price + travel_price

        # Etapa 5 & 6 — confirmar atomicamente
        accepted_at = datetime.utcnow()
        confirmed = self._service_request_repository.confirm_if_available(
            service_request_id=input_dto.service_request_id,
            accepted_provider_id=input_dto.provider_id,
            departure_address=input_dto.departure_address,
            service_price=service_price,
            travel_price=travel_price,
            total_price=total_price,
            accepted_at=accepted_at,
        )

        if confirmed is None:
            raise ServiceRequestUnavailableError()

        # Etapa 7 — notificar cliente e prestador (best effort)
        if self._notification_service is not None:
            try:
                self._notification_service.notify(confirmed)
            except Exception:
                pass

        return ConfirmServiceRequestOutputDTO(
            service_request_id=confirmed.id,
            status=confirmed.status,
            accepted_provider_id=confirmed.accepted_provider_id,
            service_price=confirmed.service_price,
            travel_price=confirmed.travel_price,
            total_price=confirmed.total_price,
            accepted_at=confirmed.accepted_at,
        )