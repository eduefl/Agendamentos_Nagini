from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ClientServiceRequestListItem:
    service_request_id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: Optional[str]
    desired_datetime: datetime
    status: str
    address: str
    created_at: Optional[datetime]
