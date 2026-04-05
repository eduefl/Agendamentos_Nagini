from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ConfirmServiceRequestInputDTO(BaseModel):
    service_request_id: UUID
    provider_id: UUID
    departure_address: str


class ConfirmServiceRequestOutputDTO(BaseModel):
    service_request_id: UUID
    status: str
    accepted_provider_id: UUID
    service_price: Decimal
    travel_price: Decimal
    total_price: Decimal
    accepted_at: datetime