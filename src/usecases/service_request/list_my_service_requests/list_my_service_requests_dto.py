from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

class ListMyServiceRequestsInputDTO(BaseModel):
    client_id: UUID


class ListMyServiceRequestsOutputItemDTO(BaseModel):
    service_request_id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str] 
    desired_datetime: datetime
    status: str
    address: str
    created_at: Optional[datetime]
    accepted_provider_id: Optional[UUID]
    service_price: Optional[Decimal]
    travel_price: Optional[Decimal]
    total_price: Optional[Decimal]
    # Fase 1 — campos do ciclo operacional
    travel_started_at: Optional[datetime] = None
    estimated_arrival_at: Optional[datetime] = None
    travel_duration_minutes: Optional[int] = None
    travel_distance_km: Optional[Decimal] = None
    provider_arrived_at: Optional[datetime] = None
    service_started_at: Optional[datetime] = None
    # Fase 1 pagamento — campos financeiros pós-serviço
    service_finished_at: Optional[datetime] = None
    payment_requested_at: Optional[datetime] = None
    payment_processing_started_at: Optional[datetime] = None
    payment_approved_at: Optional[datetime] = None
    payment_refused_at: Optional[datetime] = None
    service_concluded_at: Optional[datetime] = None
    payment_last_status: Optional[str] = None
    payment_amount: Optional[Decimal] = None    

