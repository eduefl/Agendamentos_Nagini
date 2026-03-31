from pydantic import BaseModel
from uuid import UUID


class DeactivateProviderServiceInputDTO(BaseModel):
    provider_id: UUID
    provider_service_id: UUID


class DeactivateProviderServiceOutputDTO(BaseModel):
    provider_service_id: UUID
    provider_id: UUID
    service_id: UUID
    active: bool
