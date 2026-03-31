from domain.__seedwork.exceptions import ForbiddenError
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.service.service_exceptions import ProviderServiceNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface

from usecases.service.activate_provider_service.activate_provider_service_dto import (
    ActivateProviderServiceInputDTO,
    ActivateProviderServiceOutputDTO,
)


class ActivateProviderServiceUseCase:
    def __init__(
        self,
        provider_service_repository: ProviderServiceRepositoryInterface,
        user_repository: userRepositoryInterface,
    ):
        self._provider_service_repository = provider_service_repository
        self._user_repository = user_repository

    def execute(
        self,
        input_dto: ActivateProviderServiceInputDTO,
    ) -> ActivateProviderServiceOutputDTO:
        user = self._user_repository.find_user_by_id(input_dto.provider_id)

        if not user.is_active:
            raise ForbiddenError("Usuário inativo não pode acessar esta operação")

        if not user.is_provider():
            raise ForbiddenError(
                "Apenas usuários com perfil prestador podem acessar esta operação"
            )

        provider_service = self._provider_service_repository.find_by_id(
            input_dto.provider_service_id
        )

        if provider_service is None:
            raise ProviderServiceNotFoundError()

        if provider_service.provider_id != input_dto.provider_id:
            raise ForbiddenError("Apenas o prestador dono do serviço pode ativá-lo")

        provider_service.activate()

        updated_provider_service = self._provider_service_repository.update(
            provider_service
        )

        return ActivateProviderServiceOutputDTO(
            provider_service_id=updated_provider_service.id,
            provider_id=updated_provider_service.provider_id,
            service_id=updated_provider_service.service_id,
            active=updated_provider_service.active,
        )
