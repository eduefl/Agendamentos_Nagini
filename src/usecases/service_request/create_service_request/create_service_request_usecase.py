from datetime import datetime, timedelta
from uuid import uuid4

from infrastructure.security.settings import get_settings
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.__seedwork.exceptions import ForbiddenError
from domain.service.service_exceptions import ServiceNotFoundError
from domain.service.service_repository_interface import ServiceRepositoryInterface
from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    InvalidServiceRequestDateError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service_request.create_service_request.create_service_request_dto import (
    CreateServiceRequestInputDTO,
    CreateServiceRequestOutputDTO,
)


class CreateServiceRequestUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        user_repository: userRepositoryInterface,
        service_repository: ServiceRepositoryInterface,
        provider_service_repository: ProviderServiceRepositoryInterface,
    ):
        self._service_request_repository = service_request_repository
        self._user_repository = user_repository
        self._service_repository = service_repository
        self._provider_service_repository = provider_service_repository

    def _current_reference_datetime(self, desired_datetime: datetime) -> datetime:
        if desired_datetime.tzinfo is not None:
            return datetime.now(tz=desired_datetime.tzinfo)
        return datetime.utcnow()

    def _validate_desired_datetime(self, desired_datetime: datetime) -> None:
        if desired_datetime <= self._current_reference_datetime(desired_datetime):
            raise InvalidServiceRequestDateError()

    def execute(
        self,
        input_dto: CreateServiceRequestInputDTO,
    ) -> CreateServiceRequestOutputDTO:
        user = self._user_repository.find_user_by_id(input_dto.client_id)

        if not user.is_active:
            raise ForbiddenError("Usuário inativo não pode acessar esta operação")

        if not user.is_client():
            raise ForbiddenError(
                "Apenas usuários com perfil cliente podem acessar esta operação"
            )

        service = self._service_repository.find_by_id(input_dto.service_id)
        if service is None:
            raise ServiceNotFoundError(input_dto.service_id)

        self._validate_desired_datetime(input_dto.desired_datetime)

        service_request = ServiceRequest(
            id=uuid4(),
            client_id=input_dto.client_id,
            service_id=input_dto.service_id,
            desired_datetime=input_dto.desired_datetime,
            address=input_dto.address,
        )

        created_service_request = self._service_request_repository.create(
            service_request
        )
        self._provider_service_repository.list_eligible_providers_by_service_id(
            created_service_request.service_id
        )

        # Encaixar aqui entrar os provedores elegíveis para o serviço solicitado, utilizando a lista retornada por list_eligible_providers_by_service_id

        service_request.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        settings = get_settings()
        service_request.expires_at = datetime.utcnow() + timedelta(minutes=settings.expire_minutes_request)
        created_service_request = self._service_request_repository.update(service_request)


        return CreateServiceRequestOutputDTO(
            service_request_id=created_service_request.id,
            client_id=created_service_request.client_id,
            service_id=created_service_request.service_id,
            desired_datetime=created_service_request.desired_datetime,
            status=created_service_request.status,
            address=created_service_request.address,
            created_at=created_service_request.created_at,
            expires_at=created_service_request.expires_at,
        )
