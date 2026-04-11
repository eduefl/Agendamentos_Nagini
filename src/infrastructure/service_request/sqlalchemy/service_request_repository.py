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
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.payment.sqlalchemy.payment_attempt_model import PaymentAttemptModel
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_attempt_entity import PaymentAttempt
from domain.service_request.service_request_exceptions import (
    ServiceRequestPaymentNotRequestedError,
)


class ServiceRequestRepository(ServiceRequestRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _payment_attempt_model_to_entity(self, model: PaymentAttemptModel) -> PaymentAttempt:
        return PaymentAttempt(
            id=model.id,
            service_request_id=model.service_request_id,
            attempt_number=model.attempt_number,
            amount=model.amount,
            status=model.status,
            requested_at=model.requested_at,
            processing_started_at=model.processing_started_at,
            processed_at=model.processed_at,
            approved_at=model.approved_at,
            refused_at=model.refused_at,
            provider=model.provider,
            external_reference=model.external_reference,
            refusal_reason=model.refusal_reason,
            provider_message=model.provider_message,
        )

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
            service_finished_at=model.service_finished_at,
            payment_requested_at=model.payment_requested_at,
            payment_processing_started_at=model.payment_processing_started_at,
            payment_approved_at=model.payment_approved_at,
            payment_refused_at=model.payment_refused_at,
            service_concluded_at=model.service_concluded_at,
            payment_amount=model.payment_amount,
            payment_last_status=model.payment_last_status,
            payment_provider=model.payment_provider,
            payment_reference=model.payment_reference,
            payment_attempt_count=model.payment_attempt_count,
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
            service_finished_at=entity.service_finished_at,
            payment_requested_at=entity.payment_requested_at,
            payment_processing_started_at=entity.payment_processing_started_at,
            payment_approved_at=entity.payment_approved_at,
            payment_refused_at=entity.payment_refused_at,
            service_concluded_at=entity.service_concluded_at,
            payment_amount=entity.payment_amount,
            payment_last_status=entity.payment_last_status,
            payment_provider=entity.payment_provider,
            payment_reference=entity.payment_reference,
            payment_attempt_count=entity.payment_attempt_count,
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
                service_finished_at=model.service_finished_at,
                payment_requested_at=model.payment_requested_at,
                payment_processing_started_at=model.payment_processing_started_at,
                payment_approved_at=model.payment_approved_at,
                payment_refused_at=model.payment_refused_at,
                service_concluded_at=model.service_concluded_at,
                payment_last_status=model.payment_last_status,
                payment_amount=model.payment_amount,
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
        model.service_finished_at = service_request.service_finished_at
        model.payment_requested_at = service_request.payment_requested_at
        model.payment_processing_started_at = service_request.payment_processing_started_at
        model.payment_approved_at = service_request.payment_approved_at
        model.payment_refused_at = service_request.payment_refused_at
        model.service_concluded_at = service_request.service_concluded_at
        model.payment_amount = service_request.payment_amount
        model.payment_last_status = service_request.payment_last_status
        model.payment_provider = service_request.payment_provider
        model.payment_reference = service_request.payment_reference
        model.payment_attempt_count = service_request.payment_attempt_count

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
        # Agenda operacional completa — inclui CONFIRMED e todos os status pós-confirmação, incluindo financeiros
        operational_statuses = [
            ServiceRequestStatus.CONFIRMED.value,
            ServiceRequestStatus.IN_TRANSIT.value,
            ServiceRequestStatus.ARRIVED.value,
            ServiceRequestStatus.IN_PROGRESS.value,
            ServiceRequestStatus.AWAITING_PAYMENT.value,
            ServiceRequestStatus.PAYMENT_PROCESSING.value,
            ServiceRequestStatus.COMPLETED.value,
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
                service_finished_at=sr.service_finished_at,
                payment_requested_at=sr.payment_requested_at,
                payment_last_status=sr.payment_last_status,
                service_concluded_at=sr.service_concluded_at,
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




    def finish_service_if_in_progress(
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
                ServiceRequestModel.status == ServiceRequestStatus.IN_PROGRESS.value,
            )
            .values(
                status=ServiceRequestStatus.AWAITING_PAYMENT.value,
                service_finished_at=now,
                payment_requested_at=now,
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

    def start_payment_processing_if_awaiting_payment(
        self,
        service_request_id: UUID,
        client_id: UUID,
        now: datetime,
        payment_reference: Optional[str] = None,
    ) -> Optional[ServiceRequest]:
        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.client_id == client_id,
                ServiceRequestModel.status == ServiceRequestStatus.AWAITING_PAYMENT.value,
                ServiceRequestModel.service_finished_at.isnot(None),
                ServiceRequestModel.payment_requested_at.isnot(None),
                ServiceRequestModel.payment_amount.isnot(None),
                ServiceRequestModel.payment_amount > 0,
            )
            .values(
                status=ServiceRequestStatus.PAYMENT_PROCESSING.value,
                payment_processing_started_at=now,
                payment_last_status=PaymentStatusSnapshot.PROCESSING.value,
                payment_reference=payment_reference,
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
        if model is None:
            return None
        return self._model_to_entity(model)

    def start_payment_processing_and_mark_attempt_if_awaiting_payment(
        self,
        service_request_id: UUID,
        client_id: UUID,
        attempt_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        """
        Atualiza atomicamente ServiceRequest (AWAITING_PAYMENT -> PAYMENT_PROCESSING) e
        a PaymentAttempt correspondente (REQUESTED -> PROCESSING) num único commit.

        Retorna None se a pré-condição do ServiceRequest não for satisfeita.
        Levanta ServiceRequestPaymentNotRequestedError se a pré-condição da
        PaymentAttempt não for satisfeita (rollback implícito antes de levantar).
        """
        sr_result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.client_id == client_id,
                ServiceRequestModel.status == ServiceRequestStatus.AWAITING_PAYMENT.value,
                ServiceRequestModel.service_finished_at.isnot(None),
                ServiceRequestModel.payment_requested_at.isnot(None),
                ServiceRequestModel.payment_amount.isnot(None),
                ServiceRequestModel.payment_amount > 0,
            )
            .values(
                status=ServiceRequestStatus.PAYMENT_PROCESSING.value,
                payment_processing_started_at=now,
                payment_last_status=PaymentStatusSnapshot.PROCESSING.value,
            )
            .execution_options(synchronize_session="fetch")
        )
        if sr_result.rowcount == 0:
            return None

        pa_result = self.session.execute(
            update(PaymentAttemptModel)
            .where(
                PaymentAttemptModel.id == attempt_id,
                PaymentAttemptModel.service_request_id == service_request_id,
                PaymentAttemptModel.status == PaymentAttemptStatus.REQUESTED.value,
            )
            .values(
                status=PaymentAttemptStatus.PROCESSING.value,
                processing_started_at=now,
            )
            .execution_options(synchronize_session="fetch")
        )
        if pa_result.rowcount == 0:
            self.session.rollback()
            raise ServiceRequestPaymentNotRequestedError()

        self.session.commit()

        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )
        if model is None:
            return None
        return self._model_to_entity(model)

    def mark_payment_approved_if_processing(
        self,
        service_request_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.status == ServiceRequestStatus.PAYMENT_PROCESSING.value,
            )
            .values(
                status=ServiceRequestStatus.COMPLETED.value,
                payment_approved_at=now,
                service_concluded_at=now,
                payment_last_status=PaymentStatusSnapshot.APPROVED.value,
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

    def mark_payment_refused_if_processing(
        self,
        service_request_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.status == ServiceRequestStatus.PAYMENT_PROCESSING.value,
            )
            .values(
                status=ServiceRequestStatus.AWAITING_PAYMENT.value,
                payment_refused_at=now,
                payment_last_status=PaymentStatusSnapshot.REFUSED.value,
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

    def finish_service_and_open_payment_if_in_progress(
        self,
        service_request_id: UUID,
        provider_id: UUID,
        now: datetime,
        payment_amount: Decimal,
        payment_attempt_id: UUID,
    ) -> Optional[ServiceRequest]:

        result = self.session.execute(
            update(ServiceRequestModel)
            .where(
                ServiceRequestModel.id == service_request_id,
                ServiceRequestModel.accepted_provider_id == provider_id,
                ServiceRequestModel.status == ServiceRequestStatus.IN_PROGRESS.value,
                ServiceRequestModel.service_finished_at.is_(None),
            )
            .values(
                status=ServiceRequestStatus.AWAITING_PAYMENT.value,
                service_finished_at=now,
                payment_requested_at=now,
                payment_amount=payment_amount,
                payment_last_status=PaymentStatusSnapshot.REQUESTED.value,
                payment_attempt_count=1,
                payment_reference=None,
                payment_provider=None,
                service_concluded_at=None,
            )
            .execution_options(synchronize_session="fetch")
        )

        if result.rowcount == 0:
            return None

        attempt_model = PaymentAttemptModel(
            id=payment_attempt_id,
            service_request_id=service_request_id,
            attempt_number=1,
            amount=payment_amount,
            status=PaymentAttemptStatus.REQUESTED.value,
            requested_at=now,
        )
        self.session.add(attempt_model)

        self.session.commit()

        model = (
            self.session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == service_request_id)
            .first()
        )
        return self._model_to_entity(model)    