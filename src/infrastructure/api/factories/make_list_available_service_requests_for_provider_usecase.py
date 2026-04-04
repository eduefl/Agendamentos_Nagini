from sqlalchemy.orm import Session
from infrastructure.service_request.sqlalchemy.service_request_repository import ServiceRequestRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_usecase import (
    ListAvailableServiceRequestsForProviderUseCase,
)

def make_list_available_service_requests_for_provider_usecase(
    session: Session,
) -> ListAvailableServiceRequestsForProviderUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    user_repository = userRepository(session=session)
    return ListAvailableServiceRequestsForProviderUseCase(
        service_request_repository=service_request_repository,
        user_repository=user_repository,
    )
