from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ProviderOperationalScheduleItemReadModel:
    service_request_id: UUID
    provider_id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str]
    desired_datetime: datetime
    address: str
    status: str
    service_price: Decimal
    travel_price: Decimal
    total_price: Decimal
    accepted_at: Optional[datetime]
    # Fase 1 — campos do ciclo operacional
    travel_started_at: Optional[datetime] = None
    estimated_arrival_at: Optional[datetime] = None
    travel_duration_minutes: Optional[int] = None
    provider_arrived_at: Optional[datetime] = None
    service_started_at: Optional[datetime] = None
