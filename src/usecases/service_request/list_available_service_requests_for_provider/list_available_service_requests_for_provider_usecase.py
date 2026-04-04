from domain.__seedwork.exceptions import ForbiddenError
from domain.user.user_repository_interface import userRepositoryInterface
from domain.service_request.service_request_repository_interface import ServiceRequestRepositoryInterface
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_dto import (
    ListAvailableServiceRequestsForProviderInputDTO,
    ListAvailableServiceRequestsForProviderOutputItemDTO,
)

class ListAvailableServiceRequestsForProviderUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        user_repository: userRepositoryInterface,
    ):
        self._service_request_repository = service_request_repository
        self._user_repository = user_repository

    def execute(
        self,
        input_dto: ListAvailableServiceRequestsForProviderInputDTO,
    ) -> list[ListAvailableServiceRequestsForProviderOutputItemDTO]:
        user = self._user_repository.find_user_by_id(input_dto.provider_id)
        if not user.is_active:
            raise ForbiddenError("Usuário inativo não pode acessar esta operação")
        if not user.is_provider():
            raise ForbiddenError("Apenas usuários com perfil prestador podem acessar esta operação")

        items = self._service_request_repository.list_available_for_provider(
            provider_id=input_dto.provider_id
        )
        return [
            ListAvailableServiceRequestsForProviderOutputItemDTO(
                service_request_id=item.service_request_id,    
                client_id=item.client_id,
                service_id=item.service_id,
                service_name=item.service_name,
                service_description=item.service_description,
                desired_datetime=item.desired_datetime,
                address=item.address,
                status=item.status,
                created_at=item.created_at,
                expires_at=item.expires_at,
                provider_service_id=item.provider_service_id,
                price=item.price,
                            
            )
            for item in items
        ]
