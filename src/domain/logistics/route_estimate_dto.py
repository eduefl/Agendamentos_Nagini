from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RouteEstimateDTO(BaseModel):
    duration_minutes: int
    distance_km: Optional[Decimal] = None
    estimated_arrival_at: datetime
    reference: Optional[str] = None