from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from domain.service_request.provider_operational_schedule_item_read_model import (
    ProviderOperationalScheduleItemReadModel,
)
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)
from domain.service_request.available_service_request_read_model import (
    AvailableServiceRequestReadModel,
)
from domain.service_request.service_request_exceptions import (
    ServiceRequestNotFoundError,
)
from domain.__seedwork.normalize import normalize_service_name
from domain.service_request.client_service_list_item_read_model import (
    ClientServiceRequestListItem,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from sqlalchemy import update, or_

from sqlalchemy.orm import Session

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
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
            travel_started_at=model.travel_started_at,
            route_calculated_at=model.route_calculated_at,
            estimated_arrival_at=model.estimated_arrival_at,
            travel_duration_minutes=model.travel_duration_minutes,
            travel_distance_km=model.travel_distance_km,
            provider_arrived_at=model.provider_arrived_at,
            client_confirmed_provider_arrival_at=model.client_confirmed_provider_arrival_at,
            service_started_at=model.service_started_at,
            logistics_reference=model.logistics_reference,
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
            travel_started_at=entity.travel_started_at,
            route_calculated_at=entity.route_calculated_at,
            estimated_arrival_at=entity.estimated_arrival_at,
            travel_duration_minutes=entity.travel_duration_minutes,
            travel_distance_km=entity.travel_distance_km,
            provider_arrived_at=entity.provider_arrived_at,
            client_confirmed_provider_arrival_at=entity.client_confirmed_provider_arrival_at,
            service_started_at=entity.service_started_at,
            logistics_reference=entity.logistics_reference,
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
                accepted_provider_id=model.accepted_provider_id,
                service_price=model.service_price,
                travel_price=model.travel_price,
                total_price=model.total_price,
                travel_started_at=model.travel_started_at,
                estimated_arrival_at=model.estimated_arrival_at,
                travel_duration_minutes=model.travel_duration_minutes,
                travel_distance_km=model.travel_distance_km,
                provider_arrived_at=model.provider_arrived_at,
                service_started_at=model.service_started_at,
            )
            for model, service in models
        ]

    def update(self, service_request: ServiceRequest) -> ServiceRequest:
        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request.id)
            .first()
        )

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
        model.travel_started_at = service_request.travel_started_at
        model.route_calculated_at = service_request.route_calculated_at
        model.estimated_arrival_at = service_request.estimated_arrival_at
        model.travel_duration_minutes = service_request.travel_duration_minutes
        model.travel_distance_km = service_request.travel_distance_km
        model.provider_arrived_at = service_request.provider_arrived_at
        model.client_confirmed_provider_arrival_at = (
            service_request.client_confirmed_provider_arrival_at
        )
        model.service_started_at = service_request.service_started_at
        model.logistics_reference = service_request.logistics_reference

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
            .join(
                ProviderServiceModel,
                ProviderServiceModel.service_id == ServiceRequestModel.service_id,
            )
            .join(ServiceModel, ServiceModel.id == ServiceRequestModel.service_id)
            .filter(
                ProviderServiceModel.provider_id == provider_id,
                ProviderServiceModel.active == True,
                ServiceRequestModel.status
                == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
                ServiceRequestModel.expires_at > now,
            )
            .order_by(ServiceRequestModel.created_at)
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

    def confirm_if_available(
        self,
        service_request_id: UUID,
        accepted_provider_id: UUID,
        departure_address: str,
        service_price: Decimal,
        travel_price: Decimal,
        total_price: Decimal,
        accepted_at: datetime,
    ) -> Optional[ServiceRequest]:
        now = datetime.utcnow()

        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.status
                == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
                ServiceRequestModel.expires_at > now,
            )
            .values(
                accepted_provider_id=accepted_provider_id,
                departure_address=departure_address,
                service_price=service_price,
                travel_price=travel_price,
                total_price=total_price,
                accepted_at=accepted_at,
                status=ServiceRequestStatus.CONFIRMED.value,
            )
            .execution_options(synchronize_session="fetch")
        )

        if result.rowcount == 0:
            return None

        self.session.commit()

        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )

        return self._model_to_entity(model)

    def list_operational_schedule_for_provider(
        self,
        provider_id: UUID,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[ProviderOperationalScheduleItemReadModel]:
        # Caminho B: agenda operacional completa — inclui CONFIRMED e todos os status pós-confirmação
        operational_statuses = [
            ServiceRequestStatus.CONFIRMED.value,
            ServiceRequestStatus.IN_TRANSIT.value,
            ServiceRequestStatus.ARRIVED.value,
            ServiceRequestStatus.IN_PROGRESS.value,
        ]
        query = (
            self.session.query(ServiceRequestModel, ServiceModel)
            .join(ServiceModel, ServiceModel.id == ServiceRequestModel.service_id)
            .filter(
                ServiceRequestModel.accepted_provider_id == provider_id,
                ServiceRequestModel.status.in_(operational_statuses),
            )
        )

        if start is not None:
            query = query.filter(ServiceRequestModel.desired_datetime >= start)

        if end is not None:
            query = query.filter(ServiceRequestModel.desired_datetime <= end)

        rows = query.order_by(
            ServiceRequestModel.desired_datetime.asc(),
            ServiceRequestModel.created_at.asc(),
        ).all()

        return [
            ProviderOperationalScheduleItemReadModel(
                service_request_id=sr.id,
                provider_id=sr.accepted_provider_id,
                client_id=sr.client_id,
                service_id=sr.service_id,
                service_name=normalize_service_name(svc.name),
                service_description=svc.description,
                desired_datetime=sr.desired_datetime,
                address=sr.address,
                status=sr.status,
                service_price=sr.service_price,
                travel_price=sr.travel_price,
                total_price=sr.total_price,
                accepted_at=sr.accepted_at,
                travel_started_at=sr.travel_started_at,
                estimated_arrival_at=sr.estimated_arrival_at,
                travel_duration_minutes=sr.travel_duration_minutes,
                provider_arrived_at=sr.provider_arrived_at,
                service_started_at=sr.service_started_at,
            )
            for sr, svc in rows
        ]



    def start_travel_if_confirmed(
        self,
        service_request_id: UUID,
        provider_id: UUID,
        now: datetime,
        estimated_arrival_at: datetime,
        travel_duration_minutes: int,
        travel_distance_km: Optional[Decimal],
        logistics_reference: Optional[str],
    ) -> Optional[ServiceRequest]:

        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.accepted_provider_id == provider_id,
                ServiceRequestModel.status == ServiceRequestStatus.CONFIRMED.value,
                or_(
                    ServiceRequestModel.expires_at.is_(None),
                    ServiceRequestModel.expires_at > now,
                ),
            )
            .values(
                status=ServiceRequestStatus.IN_TRANSIT.value,
                travel_started_at=now,
                route_calculated_at=now,
                estimated_arrival_at=estimated_arrival_at,
                travel_duration_minutes=travel_duration_minutes,
                travel_distance_km=travel_distance_km,
                logistics_reference=logistics_reference,
            )
            .execution_options(synchronize_session="fetch")
        )

        if result.rowcount == 0:
            return None

        self.session.commit()

        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )

        return self._model_to_entity(model)

    def mark_arrived_if_in_transit(
        self,
        service_request_id: UUID,
        provider_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:

        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.accepted_provider_id == provider_id,
                ServiceRequestModel.status == ServiceRequestStatus.IN_TRANSIT.value,
            )
            .values(
                status=ServiceRequestStatus.ARRIVED.value,
                provider_arrived_at=now,
            )
            .execution_options(synchronize_session="fetch")
        )

        if result.rowcount == 0:
            return None

        self.session.commit()

        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )

        return self._model_to_entity(model)    
    
    def confirm_provider_arrival_and_start_service_if_arrived(
        self,
        service_request_id: UUID,
        client_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.client_id == client_id,
                ServiceRequestModel.status == ServiceRequestStatus.ARRIVED.value,
            )
            .values(
                status=ServiceRequestStatus.IN_PROGRESS.value,
                client_confirmed_provider_arrival_at=now,
                service_started_at=now,
            )
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 0:
            return None
        self.session.commit()
        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )
        return self._model_to_entity(model)    