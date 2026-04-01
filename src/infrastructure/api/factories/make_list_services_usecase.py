from sqlalchemy.orm import Session

from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from usecases.service.list_services.list_services_usecase import ListServicesUseCase


def make_list_services_usecase(session: Session) -> ListServicesUseCase:
    service_repository = ServiceRepository(session)
    return ListServicesUseCase(service_repository=service_repository)
