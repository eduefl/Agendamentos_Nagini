from datetime import datetime
from enum import Enum
from typing import Optional, Union
from uuid import UUID

from domain.service_request.service_request_exceptions import (
    InvalidServiceRequestDateError,
)


class ServiceRequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    MATCHING_PROVIDER = "MATCHING_PROVIDER"
    WAITING_PROVIDER_CONFIRMATION = "WAITING_PROVIDER_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"


class ServiceRequest:
    def __init__(
        self,
        id: UUID,
        client_id: UUID,
        service_id: UUID,
        desired_datetime: datetime,
        status: str = ServiceRequestStatus.REQUESTED.value,
        address: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.client_id = client_id
        self.service_id = service_id
        self.desired_datetime = desired_datetime
        self.status = self._normalize_status(status)
        self.address = address
        self.created_at = created_at or datetime.utcnow()

        self.validate()

    def _normalize_status(self, status: Optional[Union[str, ServiceRequestStatus]]) -> str:
        if isinstance(status, ServiceRequestStatus):
            return status.value

        if isinstance(status, str):
            normalized_status = status.strip().upper()
            valid_statuses = {item.value for item in ServiceRequestStatus}

            if normalized_status in valid_statuses:
                return normalized_status

        raise ValueError("Invalid service request status.")

    def _current_reference_datetime(self) -> datetime:
        if self.desired_datetime.tzinfo is not None:
            return datetime.now(tz=self.desired_datetime.tzinfo)
        return datetime.utcnow()

    def validate(self) -> bool:
        if not isinstance(self.id, UUID):
            raise ValueError("ID must be a UUID.")

        if not isinstance(self.client_id, UUID):
            raise ValueError("Client ID must be a UUID.")

        if not isinstance(self.service_id, UUID):
            raise ValueError("Service ID must be a UUID.")

        if not isinstance(self.desired_datetime, datetime):
            raise ValueError("Desired datetime must be a datetime.")


        valid_statuses = {item.value for item in ServiceRequestStatus}
        if self.status not in valid_statuses:
            raise ValueError("Invalid service request status.")

        if self.address is not None and not isinstance(self.address, str):
            raise ValueError("Address must be a string or None.")

        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime.")

        return True
