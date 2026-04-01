from pydantic import BaseModel
from uuid import UUID

class ListServicesInputDTO(BaseModel):
    pass


class ListServicesOutputItemDTO(BaseModel):
    service_id: UUID
    name: str
    description: str
