from uuid import UUID

from pydantic import BaseModel


class ActivateProviderServiceInputDTO(BaseModel):
    provider_id: UUID
    provider_service_id: UUID


class ActivateProviderServiceOutputDTO(BaseModel):
    provider_service_id: UUID
    provider_id: UUID
    service_id: UUID
    active: bool
