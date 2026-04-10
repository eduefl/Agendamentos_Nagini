from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from domain.payment.payment_attempt_status import PaymentAttemptStatus


class PaymentResultDTO(BaseModel):
    provider: str
    external_reference: str
    status: PaymentAttemptStatus
    processed_at: datetime
    refusal_reason: Optional[str] = None
    provider_message: Optional[str] = None