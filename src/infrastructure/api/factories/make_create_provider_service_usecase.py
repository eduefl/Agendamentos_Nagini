from sqlalchemy.orm import Session

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.create_provider_service.create_provider_service_usecase import (
    CreateProviderServiceUseCase,
)


def make_create_provider_service_usecase(session: Session) -> CreateProviderServiceUseCase:
    service_repository = ServiceRepository(session=session)
    provider_service_repository = ProviderServiceRepository(session=session)
    user_repository = userRepository(session=session)

    return CreateProviderServiceUseCase(
        service_repository=service_repository,
        provider_service_repository=provider_service_repository,
        user_repository=user_repository,
        session=session,
    )
