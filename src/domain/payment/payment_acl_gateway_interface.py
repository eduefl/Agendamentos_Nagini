from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.payment.payment_dto import PaymentResultDTO


class PaymentAclGatewayInterface(ABC):
    @abstractmethod
    def process_payment(
        self,
        external_reference: str,
        amount: Decimal,
        payer_id: UUID,
        service_request_id: UUID,
        requested_at: datetime,
    ) -> PaymentResultDTO:
        raise NotImplementedError