from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class FinishServiceAndRequestPaymentInputDTO(BaseModel):
    authenticated_user_id: UUID
    service_request_id: UUID


class FinishServiceAndRequestPaymentOutputDTO(BaseModel):
    service_request_id: UUID
    status: str
    service_finished_at: datetime
    payment_requested_at: datetime
    payment_amount: Decimal
    payment_last_status: str