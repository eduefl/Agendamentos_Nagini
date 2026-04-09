from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportProviderArrivalInputDTO(BaseModel):
    authenticated_user_id: UUID
    service_request_id: UUID


class ReportProviderArrivalOutputDTO(BaseModel):
    service_request_id: UUID
    status: str
    provider_arrived_at: datetime