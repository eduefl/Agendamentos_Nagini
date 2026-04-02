from sqlalchemy.orm import Session

from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.list_my_service_requests.list_my_service_requests_usecase import (
    ListMyServiceRequestsUseCase,
)


def make_list_my_service_requests_usecase(
    session: Session,
) -> ListMyServiceRequestsUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    user_repository = userRepository(session=session)

    return ListMyServiceRequestsUseCase(
        service_request_repository=service_request_repository,
        user_repository=user_repository,
    )
