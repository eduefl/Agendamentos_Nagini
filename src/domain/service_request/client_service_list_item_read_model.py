from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

# Expandir o read model e DTOs de saída com:
# •	accepted_provider_id 
# •	service_price 
# •	travel_price 
# •	total_price 
# •	status 

@dataclass(frozen=True)
class ClientServiceRequestListItem:
    service_request_id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str]
    desired_datetime: datetime
    status: str
    address: str
    created_at: Optional[datetime]
    accepted_provider_id: Optional[UUID] = None
    service_price: Optional[Decimal] = None
    travel_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    # Fase 1 — campos do ciclo operacional
    travel_started_at: Optional[datetime] = None
    estimated_arrival_at: Optional[datetime] = None
    travel_duration_minutes: Optional[int] = None
    travel_distance_km: Optional[Decimal] = None
    provider_arrived_at: Optional[datetime] = None
    service_started_at: Optional[datetime] = None

