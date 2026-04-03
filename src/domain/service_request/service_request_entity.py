from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Union
from uuid import UUID



class ServiceRequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    AWAITING_PROVIDER_ACCEPTANCE = "AWAITING_PROVIDER_ACCEPTANCE"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


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
        accepted_provider_id: Optional[UUID] = None,
        departure_address: Optional[str] = None,
        service_price: Optional[Decimal] = None,
        travel_price: Optional[Decimal] = None,
        total_price: Optional[Decimal] = None,
        accepted_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.id = id
        self.client_id = client_id
        self.service_id = service_id
        self.desired_datetime = desired_datetime
        self.status = self._normalize_status(status)
        self.address = address
        self.created_at = created_at or datetime.utcnow()
        self.accepted_provider_id = accepted_provider_id
        self.departure_address = departure_address
        self.service_price = service_price
        self.travel_price = travel_price
        self.total_price = total_price
        self.accepted_at = accepted_at
        self.expires_at = expires_at

        self.validate()

    def _normalize_status(
        self, status: Optional[Union[str, ServiceRequestStatus]]
    ) -> str:
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

        if self.accepted_provider_id is not None and not isinstance(
            self.accepted_provider_id, UUID
        ):
            raise ValueError("Accepted provider ID must be a UUID or None.")

        if self.departure_address is not None and not isinstance(
            self.departure_address, str
        ):
            raise ValueError("Departure address must be a string or None.")

        if self.service_price is not None and not isinstance(
            self.service_price, Decimal
        ):
            raise ValueError("Service price must be a Decimal or None.")

        if self.travel_price is not None and not isinstance(self.travel_price, Decimal):
            raise ValueError("Travel price must be a Decimal or None.")
        
        if self.total_price is not None and not isinstance(self.total_price, Decimal):
            raise ValueError("Total price must be a Decimal or None.")
        

        if self.accepted_at is not None and not isinstance(self.accepted_at, datetime):
            raise ValueError("Accepted at must be a datetime or None.")

        if self.expires_at is not None and not isinstance(self.expires_at, datetime):
            raise ValueError("Expires at must be a datetime or None.")
        self._validate_non_confirmed_cancelled_state()
        self._validate_confirmed_state()
        self._validate_total_price_consistency()

        return True
    def _validate_confirmed_state(self) -> bool:
        if self.status != ServiceRequestStatus.CONFIRMED.value:
            return True

        if self.accepted_provider_id is None:
            raise ValueError("Confirmed service request must have accepted_provider_id.")

        if not self.departure_address:
            raise ValueError("Confirmed service request must have departure_address.")

        if self.service_price is None:
            raise ValueError("Confirmed service request must have service_price.")

        if self.travel_price is None:
            raise ValueError("Confirmed service request must have travel_price.")

        if self.total_price is None:
            raise ValueError("Confirmed service request must have total_price.")

        if self.accepted_at is None:
            raise ValueError("Confirmed service request must have accepted_at.")
        return True

    def _validate_total_price_consistency(self) -> bool:
        prices = [self.service_price, self.travel_price, self.total_price]

        if all(price is None for price in prices):
            return True

        if self.service_price is None or self.travel_price is None or self.total_price is None:
            raise ValueError(
                "Service price, travel price and total price must be informed together."
            )

        expected_total = self.service_price + self.travel_price
        if self.total_price != expected_total:
            raise ValueError(
                f"Total price must be equal to service_price + travel_price. "
                f"Expected {expected_total}, got {self.total_price}."
            )
        return True

    def _validate_non_confirmed_cancelled_state(self) -> bool:
        if self.status in {ServiceRequestStatus.CONFIRMED.value, ServiceRequestStatus.CANCELLED.value}:
            return True

        acceptance_fields = [
            self.accepted_provider_id,
            self.departure_address,
            self.service_price,
            self.travel_price,
            self.total_price,
            self.accepted_at,
        ]

        if any(field is not None for field in acceptance_fields):
            raise ValueError(
                "Only confirmed or cancelled service requests can have acceptance and pricing fields filled."
            )
        return True
