from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service.list_provider_services.list_provider_services_dto import (
    ListProviderServicesInputDTO,
    ListProviderServicesItemOutputDTO,
    ListProviderServicesOutputDTO,
)
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.__seedwork.exceptions import ForbiddenError


class ListProviderServicesUseCase:
    def __init__(
        self,
        provider_service_repository: ProviderServiceRepositoryInterface,
        user_repository: userRepositoryInterface,
    ):
        self._provider_service_repository = provider_service_repository
        self._user_repository = user_repository

    def execute(
        self, input_dto: ListProviderServicesInputDTO
    ) -> ListProviderServicesOutputDTO:
        user = self._user_repository.find_user_by_id(input_dto.provider_id)
        # Verificar se o usuário é prestador
        if not user.is_active:
            raise ForbiddenError("Usuário inativo não pode acessar esta operação")
        if not user.is_provider():
            raise ForbiddenError(
                "Apenas usuários com perfil prestador podem acessar esta operação"
            )

        provider_services = self._provider_service_repository.list_by_provider_id(
            input_dto.provider_id
        )

        items = [
            ListProviderServicesItemOutputDTO(
                provider_service_id=provider_service.id,
                provider_id=provider_service.provider_id,
                service_id=provider_service.service_id,
                service_name=provider_service.service_name,
                description=provider_service.service_description,
                price=provider_service.price,
                active=provider_service.active,
            )
            for provider_service in provider_services
        ]

        return ListProviderServicesOutputDTO(items=items)
