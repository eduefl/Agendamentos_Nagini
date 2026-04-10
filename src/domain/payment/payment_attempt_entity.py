from datetime import datetime
from decimal import Decimal
from typing import Optional, Union
from uuid import UUID

from domain.payment.payment_attempt_status import PaymentAttemptStatus


class PaymentAttempt:
    def __init__(
        self,
        id: UUID,
        service_request_id: UUID,
        attempt_number: int,
        amount: Decimal,
        status: str = PaymentAttemptStatus.REQUESTED.value,
        requested_at: Optional[datetime] = None,
        processing_started_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None,
        approved_at: Optional[datetime] = None,
        refused_at: Optional[datetime] = None,
        provider: Optional[str] = None,
        external_reference: Optional[str] = None,
        refusal_reason: Optional[str] = None,
        provider_message: Optional[str] = None,
    ):
        self.id = id
        self.service_request_id = service_request_id
        self.attempt_number = attempt_number
        self.amount = amount
        self.status = self._normalize_status(status)
        self.requested_at = requested_at or datetime.utcnow()
        self.processing_started_at = processing_started_at
        self.processed_at = processed_at
        self.approved_at = approved_at
        self.refused_at = refused_at
        self.provider = provider
        self.external_reference = external_reference
        self.refusal_reason = refusal_reason
        self.provider_message = provider_message

        self.validate()

    def _normalize_status(
        self, status: Optional[Union[str, PaymentAttemptStatus]]
    ) -> str:
        if isinstance(status, PaymentAttemptStatus):
            return status.value

        if isinstance(status, str):
            normalized = status.strip().upper()
            valid = {item.value for item in PaymentAttemptStatus}
            if normalized in valid:
                return normalized

        raise ValueError("Invalid payment attempt status.")

    def validate(self) -> bool:
        if not isinstance(self.id, UUID):
            raise ValueError("ID must be a UUID.")

        if not isinstance(self.service_request_id, UUID):
            raise ValueError("service_request_id must be a UUID.")

        if not isinstance(self.attempt_number, int) or self.attempt_number < 1:
            raise ValueError("attempt_number must be a positive integer.")

        if not isinstance(self.amount, Decimal) or self.amount <= Decimal("0"):
            raise ValueError("amount must be a positive Decimal.")

        valid_statuses = {item.value for item in PaymentAttemptStatus}
        if self.status not in valid_statuses:
            raise ValueError("Invalid payment attempt status.")

        if not isinstance(self.requested_at, datetime):
            raise ValueError("requested_at must be a datetime.")

        if self.processing_started_at is not None and not isinstance(self.processing_started_at, datetime):
            raise ValueError("processing_started_at must be a datetime or None.")

        if self.processed_at is not None and not isinstance(self.processed_at, datetime):
            raise ValueError("processed_at must be a datetime or None.")

        if self.approved_at is not None and not isinstance(self.approved_at, datetime):
            raise ValueError("approved_at must be a datetime or None.")

        if self.refused_at is not None and not isinstance(self.refused_at, datetime):
            raise ValueError("refused_at must be a datetime or None.")

        if self.provider is not None and not isinstance(self.provider, str):
            raise ValueError("provider must be a string or None.")

        if self.external_reference is not None and not isinstance(self.external_reference, str):
            raise ValueError("external_reference must be a string or None.")

        if self.refusal_reason is not None and not isinstance(self.refusal_reason, str):
            raise ValueError("refusal_reason must be a string or None.")

        if self.provider_message is not None and not isinstance(self.provider_message, str):
            raise ValueError("provider_message must be a string or None.")

        self._validate_state_consistency()
        self._validate_temporal_order()

        return True

    def _validate_state_consistency(self) -> bool:
        status = self.status

        if status == PaymentAttemptStatus.APPROVED.value:
            if self.approved_at is None:
                raise ValueError("APPROVED payment attempt must have approved_at.")
            if self.processed_at is None:
                raise ValueError("APPROVED payment attempt must have processed_at.")
            if self.refused_at is not None:
                raise ValueError("APPROVED payment attempt must not have refused_at.")

        if status == PaymentAttemptStatus.REFUSED.value:
            if self.refused_at is None:
                raise ValueError("REFUSED payment attempt must have refused_at.")
            if self.processed_at is None:
                raise ValueError("REFUSED payment attempt must have processed_at.")
            if self.approved_at is not None:
                raise ValueError("REFUSED payment attempt must not have approved_at.")

        if status == PaymentAttemptStatus.PROCESSING.value:
            if self.processing_started_at is None:
                raise ValueError("PROCESSING payment attempt must have processing_started_at.")

        return True

    def _validate_temporal_order(self) -> bool:
        pairs = [
            (self.requested_at, self.processing_started_at, "requested_at", "processing_started_at"),
            (self.processing_started_at, self.processed_at, "processing_started_at", "processed_at"),
            (self.processing_started_at, self.approved_at, "processing_started_at", "approved_at"),
            (self.processing_started_at, self.refused_at, "processing_started_at", "refused_at"),
        ]
        for earlier, later, earlier_name, later_name in pairs:
            if earlier is not None and later is not None and earlier > later:
                raise ValueError(f"{earlier_name} must not be after {later_name}.")
        return True