from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ListMyConfirmedScheduleInputDTO(BaseModel):
    provider_id: UUID
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class ListMyConfirmedScheduleOutputItemDTO(BaseModel):
    service_request_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str]
    client_id: UUID
    desired_datetime: datetime
    address: str
    status: str
    service_price: Decimal
    travel_price: Decimal
    total_price: Decimal
    accepted_at: Optional[datetime]