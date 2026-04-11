from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ConfirmPaymentInputDTO(BaseModel):
    authenticated_user_id: UUID
    service_request_id: UUID


class ConfirmPaymentOutputDTO(BaseModel):
    service_request_id: UUID
    status: str
    payment_processing_started_at: datetime
    payment_reference: Optional[str] = None