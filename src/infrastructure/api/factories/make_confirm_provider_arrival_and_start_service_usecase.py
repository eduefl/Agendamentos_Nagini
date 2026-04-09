from sqlalchemy.orm import Session
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from usecases.service_request.confirm_provider_arrival_and_start_service.confirm_provider_arrival_and_start_service_usecase import (
    ConfirmProviderArrivalAndStartServiceUseCase,
)
def make_confirm_provider_arrival_and_start_service_usecase(
    session: Session,
) -> ConfirmProviderArrivalAndStartServiceUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    return ConfirmProviderArrivalAndStartServiceUseCase(
        service_request_repository=service_request_repository,
    )