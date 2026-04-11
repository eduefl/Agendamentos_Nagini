from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.payment.payment_attempt_entity import PaymentAttempt


class PaymentAttemptRepositoryInterface(ABC):
    @abstractmethod
    def create(self, attempt: PaymentAttempt) -> PaymentAttempt:
        raise NotImplementedError

    @abstractmethod
    def find_latest_by_service_request_id(
        self,
        service_request_id: UUID,
    ) -> Optional[PaymentAttempt]:
        raise NotImplementedError

    @abstractmethod
    def find_by_external_reference(
        self,
        external_reference: str,
    ) -> Optional[PaymentAttempt]:
        raise NotImplementedError

    @abstractmethod
    def mark_processing(
        self,
        attempt_id: UUID,
    ) -> Optional[PaymentAttempt]:
        raise NotImplementedError

    @abstractmethod
    def mark_approved(
        self,
        attempt_id: UUID,
    ) -> Optional[PaymentAttempt]:
        raise NotImplementedError

    @abstractmethod
    def mark_refused(
        self,
        attempt_id: UUID,
        refusal_reason: Optional[str] = None,
    ) -> Optional[PaymentAttempt]:
        raise NotImplementedError

    @abstractmethod
    def count_by_service_request_id(
        self,
        service_request_id: UUID,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def record_gateway_reference(
        self,
        attempt_id: UUID,
        provider: str,
        external_reference: str,
        provider_message: Optional[str] = None,
    ) -> Optional[PaymentAttempt]:
        raise NotImplementedError