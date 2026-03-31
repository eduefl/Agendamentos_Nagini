from sqlalchemy.orm import Session

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.deactivate_provider_service.deactivate_provider_service_usecase import (
    DeactivateProviderServiceUseCase,
)


def make_deactivate_provider_service_usecase(
    session: Session,
) -> DeactivateProviderServiceUseCase:
    provider_service_repository = ProviderServiceRepository(session=session)
    user_repository = userRepository(session=session)

    return DeactivateProviderServiceUseCase(
        provider_service_repository=provider_service_repository,
        user_repository=user_repository,
    )
