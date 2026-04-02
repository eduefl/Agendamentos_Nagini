from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ListMyServiceRequestsInputDTO(BaseModel):
    client_id: UUID


class ListMyServiceRequestsOutputItemDTO(BaseModel):
    service_request_id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str] 
    desired_datetime: datetime
    status: str
    address: str
    created_at: Optional[datetime]
