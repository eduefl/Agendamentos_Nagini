from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from typing import Optional


class CreateServiceRequestInputDTO(BaseModel):
    client_id: UUID
    service_id: UUID
    desired_datetime: datetime
    address: Optional[str] = None


class CreateServiceRequestOutputDTO(BaseModel):
    service_request_id: UUID
    client_id: UUID
    service_id: UUID
    desired_datetime: datetime
    status: str
    address: Optional[str] = None
    created_at: datetime
