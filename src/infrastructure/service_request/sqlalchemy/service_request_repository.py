from datetime import datetime
from typing import Optional
from uuid import UUID

from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel
from domain.service_request.available_service_request_read_model import AvailableServiceRequestReadModel
from domain.service_request.service_request_exceptions import ServiceRequestNotFoundError
from domain.__seedwork.normalize import normalize_service_name
from domain.service_request.client_service_list_item_read_model import (
    ClientServiceRequestListItem,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from sqlalchemy.orm import Session

from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
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
            accepted_provider_id=model.accepted_provider_id,
            departure_address=model.departure_address,
            service_price=model.service_price,
            travel_price=model.travel_price,
            total_price=model.total_price,
            accepted_at=model.accepted_at,
            expires_at=model.expires_at,
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
            accepted_provider_id=entity.accepted_provider_id,
            departure_address=entity.departure_address,
            service_price=entity.service_price,
            travel_price=entity.travel_price,
            total_price=entity.total_price,
            accepted_at=entity.accepted_at,
            expires_at=entity.expires_at,            
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

    def list_by_client_id_with_service_data(
        self,
        client_id: UUID,
    ) -> list[ClientServiceRequestListItem]:
        models = (
            self.session.query(ServiceRequestModel, ServiceModel)
            .join(ServiceModel, ServiceModel.id == ServiceRequestModel.service_id)
            .filter(ServiceRequestModel.client_id == client_id)
            .order_by(ServiceRequestModel.created_at.desc())
            .all()
        )

        return [
            ClientServiceRequestListItem(
                service_request_id=model.id,
                client_id=model.client_id,
                service_id=model.service_id,
                service_name=normalize_service_name(service.name),
                service_description=service.description,
                desired_datetime=model.desired_datetime,
                status=model.status,
                address=model.address,
                created_at=model.created_at,
            )
            for model, service in models
        ]

    def update(self, service_request: ServiceRequest) -> ServiceRequest:
        model = self.session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == service_request.id
        ).first()

        if model is None:
            raise ServiceRequestNotFoundError()

        model.client_id = service_request.client_id
        model.service_id = service_request.service_id
        model.desired_datetime = service_request.desired_datetime
        model.status = service_request.status
        model.address = service_request.address
        model.accepted_provider_id = service_request.accepted_provider_id
        model.departure_address = service_request.departure_address
        model.service_price = service_request.service_price
        model.travel_price = service_request.travel_price
        model.total_price = service_request.total_price
        model.accepted_at = service_request.accepted_at
        model.expires_at = service_request.expires_at

        self.session.commit()
        self.session.refresh(model)

        return self._model_to_entity(model)
    
    
    def list_available_for_provider(
        self,
        provider_id: UUID,
    ) -> list[AvailableServiceRequestReadModel]:
        now = datetime.utcnow()
        rows = (
            self.session.query(ServiceRequestModel, ProviderServiceModel, ServiceModel)
            .join(ProviderServiceModel, ProviderServiceModel.service_id == ServiceRequestModel.service_id)
            .join(ServiceModel, ServiceModel.id == ServiceRequestModel.service_id)
            .filter(
                ProviderServiceModel.provider_id == provider_id,
                ProviderServiceModel.active == True,
                ServiceRequestModel.status == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
                ServiceRequestModel.expires_at > now,
            ).order_by(ServiceRequestModel.created_at)
            .all()
        )
        return [
            AvailableServiceRequestReadModel(
                service_request_id=sr.id,
                client_id=sr.client_id,
                service_id=sr.service_id,
                service_name=normalize_service_name(svc.name),
                service_description=svc.description,
                desired_datetime=sr.desired_datetime,
                address=sr.address,
                status=sr.status,
                created_at=sr.created_at,
                expires_at=sr.expires_at,
                provider_service_id=ps.id,
                price=ps.price,
            )
            for sr, ps, svc in rows
        ]
    