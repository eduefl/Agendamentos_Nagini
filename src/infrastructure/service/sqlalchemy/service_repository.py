from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from domain.service.service_entity import Service
from domain.service.service_exceptions import ServiceNotFoundError
from domain.service.service_repository_interface import ServiceRepositoryInterface
from infrastructure.service.sqlalchemy.service_model import ServiceModel


class ServiceRepository(ServiceRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def create_service(self, service: Service) -> None:
        normalized_name = service.name.strip().lower()
        service_model = ServiceModel(
            id=service.id,
            name=normalized_name,
            description=service.description,
        )
        self.session.add(service_model)
        self.session.flush()# o commit deve ser feito no use case para garantir atomicidade 

    def find_by_id(self, service_id: UUID) -> Service:
        service_in_db = (
            self.session.query(ServiceModel)
            .filter(ServiceModel.id == service_id)
            .first()
        )

        if not service_in_db:
            raise ServiceNotFoundError(str(service_id), attribute="id")

        return self._to_entity(service_in_db)

    def find_by_name(self, name: str) -> Optional[Service]:
        normalized_name = name.strip().lower()

        service_in_db = (
            self.session.query(ServiceModel)
            .filter(ServiceModel.name == normalized_name)
            .first()
        )

        if not service_in_db:
            return None

        return self._to_entity(service_in_db)


    @staticmethod
    def _to_entity(model: ServiceModel) -> Service:
        return Service(
            id=model.id,
            name=model.name,
            description=model.description,
        )
