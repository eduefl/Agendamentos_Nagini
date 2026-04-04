from abc import ABC, abstractmethod
from datetime import datetime
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
