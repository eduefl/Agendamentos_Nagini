from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class EligibleProviderReadModel:
    provider_id: UUID
    provider_name: str
    provider_email: str
    provider_service_id: UUID
    service_id: UUID
    price: Decimal
