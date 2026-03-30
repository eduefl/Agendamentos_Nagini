from uuid import uuid4
from domain.user.user_repository_interface import userRepositoryInterface
from domain.__seedwork.exceptions import ForbiddenError
from sqlalchemy.orm import Session

from domain.service.provider_service_entity import ProviderService
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.service.service_entity import Service
from domain.service.service_exceptions import ProviderServiceAlreadyExistsError, ServiceNotFoundError
from domain.service.service_repository_interface import ServiceRepositoryInterface
from usecases.service.create_provider_service.create_provider_service_dto import (
    CreateProviderServiceInputDTO,
    CreateProviderServiceOutputDTO,
)


class CreateProviderServiceUseCase:
    def __init__(
        self,
        service_repository: ServiceRepositoryInterface,
        provider_service_repository: ProviderServiceRepositoryInterface,
        user_repository: userRepositoryInterface,
        session: Session,
    ):
        self.service_repository = service_repository
        self.provider_service_repository = provider_service_repository
        self.user_repository = user_repository
        self.session = session

    def execute(
        self,
        input: CreateProviderServiceInputDTO,
    ) -> CreateProviderServiceOutputDTO:
        try:
            user = self.user_repository.find_user_by_id(input.provider_id)
            roles = {role.lower() for role in user.roles}
            if "prestador" not in roles:
                raise ForbiddenError("Apenas usuários com perfil prestador podem acessar esta operação")
            if input.service_id:
                service = self.service_repository.find_by_id(input.service_id)
            else:
                service = self.service_repository.find_by_name(input.name)

            if service is None:
                service = Service(
                    id=uuid4(),
                    name=input.name,
                    description=input.description,
                )
                self.service_repository.create_service(service)

            existing_provider_service = (
                self.provider_service_repository.find_by_provider_and_service(
                    provider_id=input.provider_id,
                    service_id=service.id,
                )
            )

            if existing_provider_service is not None:
                raise ProviderServiceAlreadyExistsError()

            provider_service = ProviderService(
                id=uuid4(),
                provider_id=input.provider_id,
                service_id=service.id,
                price=input.price,
                active=True,
                created_at=None,
            )

            self.provider_service_repository.create_provider_service(provider_service)

            self.session.commit() #Comito os dois repositorios

            return CreateProviderServiceOutputDTO(
                provider_service_id=provider_service.id,
                provider_id=provider_service.provider_id,
                service_id=service.id,
                service_name=service.name,
                description=service.description,
                price=provider_service.price,
                active=provider_service.active,
                created_at=provider_service.created_at,
            )
        except Exception:
            self.session.rollback()
            raise
