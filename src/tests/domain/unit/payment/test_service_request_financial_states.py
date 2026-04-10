"""
Testes unitários dos novos estados financeiros da entidade ServiceRequest.

Cobre:
- Enum ServiceRequestStatus tem AWAITING_PAYMENT, PAYMENT_PROCESSING, COMPLETED
- Aceita AWAITING_PAYMENT com campos mínimos
- Rejeita AWAITING_PAYMENT sem service_finished_at
- Rejeita AWAITING_PAYMENT sem payment_requested_at
- Rejeita AWAITING_PAYMENT com service_concluded_at
- Aceita PAYMENT_PROCESSING com campos mínimos
- Rejeita PAYMENT_PROCESSING sem payment_processing_started_at
- Rejeita PAYMENT_PROCESSING com service_concluded_at
- Aceita COMPLETED com campos mínimos
- Rejeita COMPLETED sem payment_approved_at
- Rejeita COMPLETED sem service_concluded_at
- Rejeita COMPLETED com payment_refused_at
- Rejeita ordem temporal inválida (service_started_at > service_finished_at etc.)
- Campos financeiros nulos são válidos em status pré-financeiros (ex: IN_PROGRESS)
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
import pytest

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)


# ─── helpers ────────────────────────────────────────────────────────────────


def _base_in_progress_kwargs():
    now = datetime.utcnow()
    return dict(
        id=uuid4(),
        client_id=uuid4(),
        service_id=uuid4(),
        desired_datetime=now + timedelta(days=1),
        status=ServiceRequestStatus.IN_PROGRESS,
        address="Rua das Flores, 123",
        accepted_provider_id=uuid4(),
        departure_address="Av. Paulista, 1000",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        travel_started_at=now + timedelta(minutes=5),
        route_calculated_at=now + timedelta(minutes=5),
        estimated_arrival_at=now + timedelta(minutes=30),
        travel_duration_minutes=25,
        provider_arrived_at=now + timedelta(minutes=28),
        client_confirmed_provider_arrival_at=now + timedelta(minutes=32),
        service_started_at=now + timedelta(minutes=32),
    )


def _base_awaiting_payment_kwargs():
    kwargs = _base_in_progress_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = ServiceRequestStatus.AWAITING_PAYMENT
    kwargs["service_finished_at"] = now + timedelta(hours=1)
    kwargs["payment_requested_at"] = now + timedelta(hours=1)
    return kwargs


def _base_payment_processing_kwargs():
    kwargs = _base_awaiting_payment_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = ServiceRequestStatus.PAYMENT_PROCESSING
    kwargs["payment_processing_started_at"] = now + timedelta(hours=1, minutes=1)
    return kwargs


def _base_completed_kwargs():
    kwargs = _base_payment_processing_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = ServiceRequestStatus.COMPLETED
    kwargs["payment_last_status"] = PaymentStatusSnapshot.APPROVED.value
    kwargs["payment_approved_at"] = now + timedelta(hours=1, minutes=2)
    kwargs["service_concluded_at"] = now + timedelta(hours=1, minutes=2)
    return kwargs


# ─── Enum ────────────────────────────────────────────────────────────────────


class TestFinancialStatusEnum:
    def test_enum_has_awaiting_payment(self):
        assert ServiceRequestStatus.AWAITING_PAYMENT.value == "AWAITING_PAYMENT"

    def test_enum_has_payment_processing(self):
        assert ServiceRequestStatus.PAYMENT_PROCESSING.value == "PAYMENT_PROCESSING"

    def test_enum_has_completed(self):
        assert ServiceRequestStatus.COMPLETED.value == "COMPLETED"

    def test_entity_accepts_awaiting_payment_as_string(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["status"] = "AWAITING_PAYMENT"
        sr = ServiceRequest(**kwargs)
        assert sr.status == "AWAITING_PAYMENT"

    def test_entity_accepts_payment_processing_as_string(self):
        kwargs = _base_payment_processing_kwargs()
        kwargs["status"] = "PAYMENT_PROCESSING"
        sr = ServiceRequest(**kwargs)
        assert sr.status == "PAYMENT_PROCESSING"

    def test_entity_accepts_completed_as_string(self):
        kwargs = _base_completed_kwargs()
        kwargs["status"] = "COMPLETED"
        sr = ServiceRequest(**kwargs)
        assert sr.status == "COMPLETED"


# ─── AWAITING_PAYMENT ────────────────────────────────────────────────────────


class TestAwaitingPaymentState:
    def test_valid_awaiting_payment(self):
        sr = ServiceRequest(**_base_awaiting_payment_kwargs())
        assert sr.status == "AWAITING_PAYMENT"
        assert sr.service_finished_at is not None
        assert sr.payment_requested_at is not None
        assert sr.service_concluded_at is None

    def test_rejects_without_service_finished_at(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["service_finished_at"] = None
        with pytest.raises(ValueError, match="must have service_finished_at"):
            ServiceRequest(**kwargs)

    def test_rejects_without_payment_requested_at(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["payment_requested_at"] = None
        with pytest.raises(ValueError, match="must have payment_requested_at"):
            ServiceRequest(**kwargs)

    def test_rejects_without_service_started_at(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["service_started_at"] = None
        with pytest.raises(ValueError, match="must have service_started_at"):
            ServiceRequest(**kwargs)

    def test_rejects_with_service_concluded_at(self):
        kwargs = _base_awaiting_payment_kwargs()
        now = datetime.utcnow()
        kwargs["service_concluded_at"] = now + timedelta(hours=2)
        with pytest.raises(ValueError, match="must not have service_concluded_at"):
            ServiceRequest(**kwargs)

    def test_rejects_with_payment_approved_at(self):
        kwargs = _base_awaiting_payment_kwargs()
        now = datetime.utcnow()
        kwargs["payment_approved_at"] = now + timedelta(hours=2)
        with pytest.raises(ValueError, match="must not have payment_approved_at"):
            ServiceRequest(**kwargs)

    def test_financial_fields_are_none_by_default_in_in_progress(self):
        sr = ServiceRequest(**_base_in_progress_kwargs())
        assert sr.service_finished_at is None
        assert sr.payment_requested_at is None
        assert sr.payment_processing_started_at is None
        assert sr.payment_approved_at is None
        assert sr.payment_refused_at is None
        assert sr.service_concluded_at is None
        assert sr.payment_amount is None
        assert sr.payment_last_status is None
        assert sr.payment_provider is None
        assert sr.payment_reference is None
        assert sr.payment_attempt_count is None

    def test_rejects_in_progress_with_service_finished_at(self):
        kwargs = _base_in_progress_kwargs()
        now = datetime.utcnow()
        kwargs["service_finished_at"] = now + timedelta(hours=1)
        with pytest.raises(
            ValueError, match="must not have financial post-service fields set"
        ):
            ServiceRequest(**kwargs)


    def test_rejects_in_progress_with_payment_amount(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["payment_amount"] = Decimal("120.00")
        with pytest.raises(
            ValueError, match="must not have financial post-service fields set"
        ):
            ServiceRequest(**kwargs)

    def test_rejects_in_progress_with_payment_last_status(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["payment_last_status"] = "APPROVED"
        with pytest.raises(
            ValueError, match="must not have financial post-service fields set"
        ):
            ServiceRequest(**kwargs)

    def test_rejects_in_progress_with_payment_provider(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["payment_provider"] = "mock-provider"
        with pytest.raises(
            ValueError, match="must not have financial post-service fields set"
        ):
            ServiceRequest(**kwargs)

    def test_rejects_in_progress_payment_reference(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["payment_reference"] = "ref-123"
        with pytest.raises(
            ValueError, match="must not have financial post-service fields set"
        ):
            ServiceRequest(**kwargs)

    def test_rejects_in_progress_payment_attempt_count(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["payment_attempt_count"] = 1
        with pytest.raises(
            ValueError, match="must not have financial post-service fields set"
        ):
            ServiceRequest(**kwargs)


# ─── payment_last_status validation ──────────────────────────────────────────


class TestPaymentLastStatusValidation:
    def test_rejects_invalid_payment_last_status_value(self):
        kwargs = _base_completed_kwargs()
        kwargs["payment_last_status"] = "COMPLETED"  # ServiceRequest status — wrong
        with pytest.raises(ValueError, match="payment_last_status must be one of"):
            ServiceRequest(**kwargs)

    def test_rejects_service_request_status_as_payment_last_status(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["payment_last_status"] = "AWAITING_PAYMENT"  # Wrong semantic
        with pytest.raises(ValueError, match="payment_last_status must be one of"):
            ServiceRequest(**kwargs)

    def test_accepts_approved_as_payment_last_status(self):
        kwargs = _base_completed_kwargs()
        kwargs["payment_last_status"] = "APPROVED"
        sr = ServiceRequest(**kwargs)
        assert sr.payment_last_status == "APPROVED"

    def test_accepts_refused_as_payment_last_status(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["payment_last_status"] = "REFUSED"
        sr = ServiceRequest(**kwargs)
        assert sr.payment_last_status == "REFUSED"

    def test_payment_amount_must_be_positive(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["payment_amount"] = Decimal("0")
        with pytest.raises(
            ValueError, match="payment_amount must be greater than zero"
        ):
            ServiceRequest(**kwargs)

    def test_payment_amount_negative_rejected(self):
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["payment_amount"] = Decimal("-1.00")
        with pytest.raises(
            ValueError, match="payment_amount must be greater than zero"
        ):
            ServiceRequest(**kwargs)


# ─── PAYMENT_PROCESSING ──────────────────────────────────────────────────────


class TestPaymentProcessingState:
    def test_valid_payment_processing(self):
        sr = ServiceRequest(**_base_payment_processing_kwargs())
        assert sr.status == "PAYMENT_PROCESSING"
        assert sr.payment_processing_started_at is not None

    def test_rejects_without_payment_processing_started_at(self):
        kwargs = _base_payment_processing_kwargs()
        kwargs["payment_processing_started_at"] = None
        with pytest.raises(ValueError, match="must have payment_processing_started_at"):
            ServiceRequest(**kwargs)

    def test_rejects_without_service_finished_at(self):
        kwargs = _base_payment_processing_kwargs()
        kwargs["service_finished_at"] = None
        with pytest.raises(ValueError, match="must have service_finished_at"):
            ServiceRequest(**kwargs)

    def test_rejects_with_service_concluded_at(self):
        kwargs = _base_payment_processing_kwargs()
        now = datetime.utcnow()
        kwargs["service_concluded_at"] = now + timedelta(hours=2)
        with pytest.raises(ValueError, match="must not have service_concluded_at"):
            ServiceRequest(**kwargs)

    def test_rejects_with_payment_approved_at(self):
        kwargs = _base_payment_processing_kwargs()
        now = datetime.utcnow()
        kwargs["payment_approved_at"] = now + timedelta(hours=2)
        with pytest.raises(ValueError, match="must not have payment_approved_at"):
            ServiceRequest(**kwargs)


# ─── COMPLETED ───────────────────────────────────────────────────────────────


class TestCompletedState:
    def test_valid_completed(self):
        sr = ServiceRequest(**_base_completed_kwargs())
        assert sr.status == "COMPLETED"
        assert sr.service_finished_at is not None
        assert sr.payment_approved_at is not None
        assert sr.service_concluded_at is not None
        assert sr.payment_refused_at is None

    def test_rejects_without_payment_approved_at(self):
        kwargs = _base_completed_kwargs()
        kwargs["payment_approved_at"] = None
        with pytest.raises(ValueError, match="must have payment_approved_at"):
            ServiceRequest(**kwargs)

    def test_rejects_payment_last_status_Not_Approved(self):
        kwargs = _base_completed_kwargs()
        kwargs["payment_last_status"] = PaymentStatusSnapshot.REFUSED.value
        with pytest.raises(
            ValueError,
            match="COMPLETED service request must have payment_last_status = APPROVED.",
        ):
            ServiceRequest(**kwargs)

    def test_rejects_without_service_concluded_at(self):
        kwargs = _base_completed_kwargs()
        kwargs["service_concluded_at"] = None
        with pytest.raises(ValueError, match="must have service_concluded_at"):
            ServiceRequest(**kwargs)

    def test_rejects_without_service_finished_at(self):
        kwargs = _base_completed_kwargs()
        kwargs["service_finished_at"] = None
        with pytest.raises(ValueError, match="must have service_finished_at"):
            ServiceRequest(**kwargs)

    def test_rejects_with_payment_refused_at(self):
        kwargs = _base_completed_kwargs()
        now = datetime.utcnow()
        kwargs["payment_refused_at"] = now + timedelta(hours=1, minutes=1)
        with pytest.raises(ValueError, match="must not have payment_refused_at"):
            ServiceRequest(**kwargs)

    def test_accepts_optional_payment_fields(self):
        kwargs = _base_completed_kwargs()
        kwargs["payment_amount"] = Decimal("120.00")
        kwargs["payment_last_status"] = "APPROVED"
        kwargs["payment_provider"] = "mock-provider"
        kwargs["payment_reference"] = "ref-123"
        kwargs["payment_attempt_count"] = 1
        sr = ServiceRequest(**kwargs)
        assert sr.payment_amount == Decimal("120.00")
        assert sr.payment_last_status == "APPROVED"
        assert sr.payment_provider == "mock-provider"
        assert sr.payment_reference == "ref-123"
        assert sr.payment_attempt_count == 1


# ─── Coerência temporal financeira ───────────────────────────────────────────


class TestFinancialTemporalOrder:
    def test_rejects_service_finished_before_service_started(self):
        now = datetime.utcnow()
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["service_started_at"] = now + timedelta(hours=2)
        kwargs["service_finished_at"] = now + timedelta(hours=1)
        kwargs["payment_requested_at"] = now + timedelta(hours=2, minutes=1)
        with pytest.raises(
            ValueError, match="service_started_at must not be after service_finished_at"
        ):
            ServiceRequest(**kwargs)

    def test_rejects_payment_requested_before_service_finished(self):
        now = datetime.utcnow()
        kwargs = _base_awaiting_payment_kwargs()
        kwargs["service_finished_at"] = now + timedelta(hours=2)
        kwargs["payment_requested_at"] = now + timedelta(hours=1)
        with pytest.raises(
            ValueError,
            match="service_finished_at must not be after payment_requested_at",
        ):
            ServiceRequest(**kwargs)

    def test_rejects_payment_processing_before_payment_requested(self):
        now = datetime.utcnow()
        kwargs = _base_payment_processing_kwargs()
        kwargs["payment_requested_at"] = now + timedelta(hours=2)
        kwargs["payment_processing_started_at"] = now + timedelta(hours=1)
        with pytest.raises(
            ValueError,
            match="payment_requested_at must not be after payment_processing_started_at",
        ):
            ServiceRequest(**kwargs)

    def test_rejects_payment_approved_before_processing_started(self):
        now = datetime.utcnow()
        kwargs = _base_completed_kwargs()
        kwargs["payment_processing_started_at"] = now + timedelta(hours=2)
        kwargs["payment_approved_at"] = now + timedelta(hours=1)
        kwargs["service_concluded_at"] = now + timedelta(hours=2, minutes=1)
        with pytest.raises(
            ValueError,
            match="payment_processing_started_at must not be after payment_approved_at",
        ):
            ServiceRequest(**kwargs)

    def test_rejects_service_concluded_before_payment_approved(self):
        now = datetime.utcnow()
        kwargs = _base_completed_kwargs()
        kwargs["payment_approved_at"] = now + timedelta(hours=2)
        kwargs["service_concluded_at"] = now + timedelta(hours=1)
        with pytest.raises(
            ValueError,
            match="payment_approved_at must not be after service_concluded_at",
        ):
            ServiceRequest(**kwargs)

    def test_rejects_payment_refused_before_processing_started(self):
        now = datetime.utcnow()
        kwargs = _base_awaiting_payment_kwargs()
        # transition back from PAYMENT_PROCESSING to AWAITING_PAYMENT with refused
        kwargs["payment_processing_started_at"] = now + timedelta(hours=2)
        kwargs["payment_refused_at"] = now + timedelta(hours=1)
        with pytest.raises(
            ValueError,
            match="payment_processing_started_at must not be after payment_refused_at",
        ):
            ServiceRequest(**kwargs)
