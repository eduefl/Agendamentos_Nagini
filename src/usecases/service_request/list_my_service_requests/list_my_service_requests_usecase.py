from domain.__seedwork.exceptions import ForbiddenError
from domain.user.user_repository_interface import userRepositoryInterface
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.list_my_service_requests.list_my_service_requests_dto import (
    ListMyServiceRequestsInputDTO,
    ListMyServiceRequestsOutputItemDTO,
)


class ListMyServiceRequestsUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        user_repository: userRepositoryInterface,
    ):
        self.service_request_repository = service_request_repository
        self._user_repository = user_repository

    def execute(
        self,
        input_dto: ListMyServiceRequestsInputDTO,
    ) -> list[ListMyServiceRequestsOutputItemDTO]:

        user = self._user_repository.find_user_by_id(input_dto.client_id)
        if not user.is_active:
            raise ForbiddenError("Usuário inativo não pode acessar esta operação")

        if not user.is_client():
            raise ForbiddenError(
                "Apenas usuários com perfil cliente podem acessar esta operação"
            )

        items = self.service_request_repository.list_by_client_id_with_service_data(
            client_id=input_dto.client_id
        )

        return [
            ListMyServiceRequestsOutputItemDTO(
                service_request_id=item.service_request_id,
                client_id=item.client_id,
                service_id=item.service_id,
                service_name=item.service_name,
                service_description=item.service_description,
                desired_datetime=item.desired_datetime,
                status=item.status,
                address=item.address,
                created_at=item.created_at,
                accepted_provider_id=item.accepted_provider_id,
                service_price=item.service_price,
                travel_price=item.travel_price,
                total_price=item.total_price,
                travel_started_at=item.travel_started_at,
                estimated_arrival_at=item.estimated_arrival_at,
                travel_duration_minutes=item.travel_duration_minutes,
                travel_distance_km=item.travel_distance_km,
                provider_arrived_at=item.provider_arrived_at,
                service_started_at=item.service_started_at,
            )
            for item in items
        ]