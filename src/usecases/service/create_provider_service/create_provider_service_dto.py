from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, root_validator


class CreateProviderServiceInputDTO(BaseModel):
    provider_id: UUID
    name: Optional[str] = None
    service_id: Optional[UUID] = None
    description: Optional[str] = None
    price: Decimal

    @root_validator(pre=True)
    def normalize_empty_strings(cls, values):
        if values.get("service_id") == "":
            values["service_id"] = None

        if values.get("name") == "":
            values["name"] = None

        return values

    @root_validator
    def validate_name_xor_service_id(cls, values):
        name = values.get("name")
        service_id = values.get("service_id")

        has_name = name is not None and name.strip() != ""
        has_service_id = service_id is not None

        if has_name == has_service_id:
            raise ValueError("Informe um 'name' para um servico ou um 'service_id' de um servico ja cadastrado.")

        if has_name:
            values["name"] = name.strip()

        return values


class CreateProviderServiceOutputDTO(BaseModel):
    provider_service_id: UUID
    provider_id: UUID
    service_id: UUID
    service_name: str
    description: Optional[str] = None
    price: Decimal
    active: bool
    created_at: datetime
