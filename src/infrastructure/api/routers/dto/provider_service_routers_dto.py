from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, root_validator


class CreateProviderServiceRequestDTO(BaseModel):
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

