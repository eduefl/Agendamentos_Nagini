from datetime import datetime

from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ClientNotAllowedToConfirmProviderArrivalError,
    ServiceRequestArrivalAlreadyConfirmedError,
    ServiceRequestNotArrivedError,
    ServiceRequestNotFoundError,
    ServiceRequestProviderArrivalNotRegisteredError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.confirm_provider_arrival_and_start_service.confirm_provider_arrival_and_start_service_dto import (
    ConfirmProviderArrivalAndStartServiceInputDTO,
    ConfirmProviderArrivalAndStartServiceOutputDTO,
)


class ConfirmProviderArrivalAndStartServiceUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
    ):
        self._service_request_repository = service_request_repository

    def execute(
        self,
        input_dto: ConfirmProviderArrivalAndStartServiceInputDTO,
    ) -> ConfirmProviderArrivalAndStartServiceOutputDTO:
        # 1. Buscar ServiceRequest por id
        service_request = self._service_request_repository.find_by_id(
            input_dto.service_request_id
        )
        if service_request is None:
            raise ServiceRequestNotFoundError()

        # 2. Validar que o usuário autenticado é o cliente dono
        if service_request.client_id != input_dto.authenticated_user_id:
            raise ClientNotAllowedToConfirmProviderArrivalError()

        # 3. Verificar se já está IN_PROGRESS (confirmação duplicada)
        if service_request.status == ServiceRequestStatus.IN_PROGRESS.value:
            raise ServiceRequestArrivalAlreadyConfirmedError()

        # 4. Validar que o status atual é ARRIVED
        if service_request.status != ServiceRequestStatus.ARRIVED.value:
            raise ServiceRequestNotArrivedError()

        # 5. Validar que provider_arrived_at existe
        if service_request.provider_arrived_at is None:
            raise ServiceRequestProviderArrivalNotRegisteredError()

        # 6. Capturar now (mesmo timestamp para os dois campos)
        now = datetime.utcnow()

        # 7. Update condicional atômico: ARRIVED → IN_PROGRESS
        updated = self._service_request_repository.confirm_provider_arrival_and_start_service_if_arrived(
            service_request_id=input_dto.service_request_id,
            client_id=input_dto.authenticated_user_id,
            now=now,
        )

        # 8. Se o update falhar, reler e reclassificar
        if updated is None:
            current = self._service_request_repository.find_by_id(
                input_dto.service_request_id
            )

            if current is None:
                raise ServiceRequestNotFoundError()

            if current.client_id != input_dto.authenticated_user_id:
                raise ClientNotAllowedToConfirmProviderArrivalError()

            if current.status == ServiceRequestStatus.IN_PROGRESS.value:
                raise ServiceRequestArrivalAlreadyConfirmedError()

            if current.status != ServiceRequestStatus.ARRIVED.value:
                raise ServiceRequestNotArrivedError()

            if current.provider_arrived_at is None:
                raise ServiceRequestProviderArrivalNotRegisteredError()

            # Status is ARRIVED and provider_arrived_at is set, but the conditional
            # update still missed (e.g. an extreme race between two concurrent requests).
            # Treat as a non-ARRIVED state for the caller.
            raise ServiceRequestNotArrivedError()

        # 9. Retornar output DTO com IN_PROGRESS
        return ConfirmProviderArrivalAndStartServiceOutputDTO(
            service_request_id=updated.id,
            status=updated.status,
            client_confirmed_provider_arrival_at=updated.client_confirmed_provider_arrival_at,
            service_started_at=updated.service_started_at,
        )