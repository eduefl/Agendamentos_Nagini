from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

class EmailSenderInterface(ABC):
    @abstractmethod
    def send_activation_email(self, to_email: str, activation_code: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def send_service_request_notification_email(
        self,
        to_email: str,
        provider_name: str,
        service_name: str,
        desired_datetime: datetime,
        address: Optional[str],
        expires_at: Optional[datetime],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_service_request_confirmed_to_client(
        self,
        client_email: str,
        client_name: str,
        service_name: str,
        service_price: Decimal,
        travel_price: Decimal,
        total_price: Decimal,
        status: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_service_request_confirmed_to_provider(
        self,
        provider_email: str,
        provider_name: str,
        service_name: str,
        service_price: Decimal,
        service_address: Optional[str],
        travel_price: Decimal,
        total_price: Decimal,
    ) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def send_travel_started_to_client(
        self,
        client_email: str,
        client_name: str,
        estimated_arrival_at: datetime,
        travel_duration_minutes: int,
    ) -> None:
        raise NotImplementedError    

    @abstractmethod
    def send_provider_arrived_to_client(
        self,
        client_email: str,
        client_name: str,
        provider_arrived_at: datetime,
    ) -> None:
        raise NotImplementedError        