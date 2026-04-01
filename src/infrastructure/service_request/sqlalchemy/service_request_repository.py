from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from domain.service_request.service_request_entity import ServiceRequest
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)


class ServiceRequestRepository(ServiceRequestRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _model_to_entity(
        self,
        model: ServiceRequestModel,
    ) -> ServiceRequest:
        return ServiceRequest(
            id=model.id,
            client_id=model.client_id,
            service_id=model.service_id,
            desired_datetime=model.desired_datetime,
            status=model.status,
            address=model.address,
            created_at=model.created_at,
        )

    def _entity_to_model(
        self,
        entity: ServiceRequest,
    ) -> ServiceRequestModel:
        return ServiceRequestModel(
            id=entity.id,
            client_id=entity.client_id,
            service_id=entity.service_id,
            desired_datetime=entity.desired_datetime,
            status=entity.status,
            address=entity.address,
            created_at=entity.created_at,
        )

    def create(
        self,
        service_request: ServiceRequest,
    ) -> ServiceRequest:
        model = self._entity_to_model(service_request)

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return self._model_to_entity(model)

    def find_by_id(
        self,
        service_request_id: UUID,
    ) -> Optional[ServiceRequest]:
        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )

        if model is None:
            return None

        return self._model_to_entity(model)

    def list_by_client_id(
        self,
        client_id: UUID,
    ) -> list[ServiceRequest]:
        models = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.client_id == client_id)
            .order_by(ServiceRequestModel.created_at.desc())
            .all()
        )

        return [self._model_to_entity(model) for model in models]
