from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class AvailableServiceRequestReadModel:
    service_request_id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str]
    desired_datetime: datetime
    address: Optional[str]
    status: str
    created_at: Optional[datetime]
    expires_at: Optional[datetime]
    provider_service_id: UUID    # ID do ProviderService do prestador logado
    price: Decimal               # Preço do prestador para este serviço

