from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from domain.service.service_exceptions import (
    ProviderServiceAlreadyActiveError,
    ProviderServiceAlreadyInactiveError,
)


class ProviderService:
    id: UUID
    provider_id: UUID
    service_id: UUID
    price: Decimal
    active: bool
    created_at: Optional[datetime] = None

    def __init__(
        self,
        id: UUID,
        provider_id: UUID,
        service_id: UUID,
        price: Decimal,
        active: bool = True,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.provider_id = provider_id
        self.service_id = service_id
        self.price = price
        self.active = active
        self.created_at = created_at if created_at is not None else datetime.utcnow()
        self.validate()

    def validate(self) -> bool:
        if not isinstance(self.id, UUID):
            raise ValueError("ID must be a valid UUID.")

        if not isinstance(self.provider_id, UUID):
            raise ValueError("Provider ID must be a valid UUID.")

        if not isinstance(self.service_id, UUID):
            raise ValueError("Service ID must be a valid UUID.")

        if not isinstance(self.price, Decimal):
            raise ValueError("Price must be a Decimal.")
        if self.price < 0:
            raise ValueError("Price cannot be negative.")

        if not isinstance(self.active, bool):
            raise ValueError("Active must be a boolean.")

        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime.")
        return True

    def deactivate(self) -> None:
        if not self.active:
            raise ProviderServiceAlreadyInactiveError()
        self.active = False

    def activate(self) -> None:
        if self.active:
            raise ProviderServiceAlreadyActiveError()
        self.active = True
