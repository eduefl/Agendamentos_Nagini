from decimal import Decimal
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class CreateProviderServiceInputDTO(BaseModel):
	provider_id: UUID
	name: str = Field(min_length=1)
	description: Optional[str] = None
	price: Decimal

class CreateProviderServiceOutputDTO(BaseModel):
    provider_service_id: UUID
    provider_id: UUID
    service_id: UUID
    service_name: str
    description: Optional[str] = None
    price: Decimal
    active: bool
    created_at: datetime
