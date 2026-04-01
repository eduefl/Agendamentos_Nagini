from sqlalchemy.orm import Session

from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.create_service_request.create_service_request_usecase import (
    CreateServiceRequestUseCase,
)


def make_create_service_request_usecase(
    session: Session,
) -> CreateServiceRequestUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    service_repository = ServiceRepository(session=session)
    user_repository = userRepository(session=session)

    return CreateServiceRequestUseCase(
        service_request_repository=service_request_repository,
        user_repository=user_repository,
        service_repository=service_repository,
    )
