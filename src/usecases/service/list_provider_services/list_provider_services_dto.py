from decimal import Decimal
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class ListProviderServicesInputDTO(BaseModel):
    provider_id: UUID


class ListProviderServicesItemOutputDTO(BaseModel):
    provider_service_id: UUID
    provider_id: UUID
    service_id: UUID
    service_name: str
    description: Optional[str]
    price: Decimal
    active: bool


class ListProviderServicesOutputDTO(BaseModel):
    items: list[ListProviderServicesItemOutputDTO]


