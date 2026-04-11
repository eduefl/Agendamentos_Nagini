from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ServiceRequestNotificationGatewayInterface(ABC):
    @abstractmethod
    def notify_client_travel_started(
        self,
        client_id: UUID,
        service_request_id: UUID,
        estimated_arrival_at: datetime,
        travel_duration_minutes: int,
    ) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def notify_client_provider_arrived(
        self,
        client_id: UUID,
        service_request_id: UUID,
        provider_arrived_at: datetime,
    ) -> None:
        raise NotImplementedError    
    

    @abstractmethod
    def notify_payment_requested(
        self,
        client_id: UUID,
        service_request_id: UUID,
        payment_amount: Decimal,
        payment_requested_at: datetime,
    ) -> None:
        raise NotImplementedError        