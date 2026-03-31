from sqlalchemy.orm import Session

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.list_provider_services.list_provider_services_usecase import (
    ListProviderServicesUseCase,
)


def make_list_provider_services_usecase(
    session: Session,
) -> ListProviderServicesUseCase:
    provider_service_repository = ProviderServiceRepository(session=session)
    user_repository = userRepository(session=session)

    return ListProviderServicesUseCase(
        provider_service_repository=provider_service_repository,
        user_repository=user_repository,
    )
