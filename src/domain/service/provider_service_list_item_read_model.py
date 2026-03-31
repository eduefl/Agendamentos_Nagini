from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ProviderServiceListItem:
    id: UUID
    provider_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str]
    price: Decimal
    active: bool
    created_at: Optional[datetime]
