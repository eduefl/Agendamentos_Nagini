from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
class ConfirmProviderArrivalAndStartServiceInputDTO(BaseModel):
    authenticated_user_id: UUID
    service_request_id: UUID
class ConfirmProviderArrivalAndStartServiceOutputDTO(BaseModel):
    service_request_id: UUID
    status: str
    client_confirmed_provider_arrival_at: datetime
    service_started_at: datetime