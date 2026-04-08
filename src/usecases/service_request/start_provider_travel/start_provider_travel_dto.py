from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StartProviderTravelInputDTO(BaseModel):
    authenticated_user_id: UUID
    service_request_id: UUID


class StartProviderTravelOutputDTO(BaseModel):
    service_request_id: UUID
    status: str
    travel_started_at: datetime
    estimated_arrival_at: datetime
    travel_duration_minutes: int
    travel_distance_km: Optional[Decimal] = None