from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from domain.service_request.provider_operational_schedule_item_read_model import (
    ProviderOperationalScheduleItemReadModel,
)
from domain.service_request.available_service_request_read_model import (
    AvailableServiceRequestReadModel,
)
from domain.service_request.client_service_list_item_read_model import (
    ClientServiceRequestListItem,
)
from domain.service_request.service_request_entity import ServiceRequest


class ServiceRequestRepositoryInterface(ABC):
    @abstractmethod
    def create(self, service_request: ServiceRequest) -> ServiceRequest:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(
        self,
        service_request_id: UUID,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def list_by_client_id(
        self,
        client_id: UUID,
    ) -> list[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def list_by_client_id_with_service_data(
        self,
        client_id: UUID,
    ) -> list[ClientServiceRequestListItem]:
        raise NotImplementedError

    @abstractmethod
    def update(self, service_request: ServiceRequest) -> ServiceRequest:
        raise NotImplementedError

    @abstractmethod
    def list_available_for_provider(
        self,
        provider_id: UUID,
    ) -> list[AvailableServiceRequestReadModel]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def list_operational_schedule_for_provider(
        self,
        provider_id: UUID,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[ProviderOperationalScheduleItemReadModel]:
        raise NotImplementedError


    @abstractmethod
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
        raise NotImplementedError


    @abstractmethod
    def mark_arrived_if_in_transit(
        self,
        service_request_id: UUID,
        provider_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError        
    
    @abstractmethod
    def confirm_provider_arrival_and_start_service_if_arrived(
        self,
        service_request_id: UUID,
        client_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def finish_service_if_in_progress(
        self,
        service_request_id: UUID,
        provider_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def start_payment_processing_if_awaiting_payment(
        self,
        service_request_id: UUID,
        now: datetime,
        payment_reference: Optional[str] = None,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def mark_payment_approved_if_processing(
        self,
        service_request_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def mark_payment_refused_if_processing(
        self,
        service_request_id: UUID,
        now: datetime,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError            