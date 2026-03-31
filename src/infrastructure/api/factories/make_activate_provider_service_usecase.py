from sqlalchemy.orm import Session

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.activate_provider_service.activate_provider_service_usecase import (
    ActivateProviderServiceUseCase,
)


def make_activate_provider_service_usecase(
    session: Session,
) -> ActivateProviderServiceUseCase:
    provider_service_repository = ProviderServiceRepository(session=session)
    user_repository = userRepository(session=session)

    return ActivateProviderServiceUseCase(
        provider_service_repository=provider_service_repository,
        user_repository=user_repository,
    )
