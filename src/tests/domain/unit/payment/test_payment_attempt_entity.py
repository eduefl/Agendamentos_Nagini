"""
Testes unitários da entidade PaymentAttempt.
Cobre:
- Cria tentativa com status REQUESTED
- Aceita transição REQUESTED -> PROCESSING
- Aceita PROCESSING -> APPROVED
- Aceita PROCESSING -> REFUSED
- Rejeita transições inválidas (status inválido)
- Rejeita APPROVED sem approved_at
- Rejeita REFUSED sem refused_at
- Rejeita APPROVED com refused_at
- Rejeita REFUSED com approved_at
- Rejeita PROCESSING sem processing_started_at
- Rejeita ordem temporal inválida
- Persiste external_reference, provider e refusal_reason
- Rejeita attempt_number <= 0
- Rejeita amount <= 0
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import pytest
from domain.payment.payment_attempt_entity import PaymentAttempt
from domain.payment.payment_attempt_status import PaymentAttemptStatus


# ─── helpers ────────────────────────────────────────────────────────────────
def _base_requested_kwargs():
    now = datetime.utcnow()
    return dict(
        id=uuid4(),
        service_request_id=uuid4(),
        attempt_number=1,
        amount=Decimal("120.00"),
        status=PaymentAttemptStatus.REQUESTED,
        requested_at=now,
    )


def _base_processing_kwargs():
    kwargs = _base_requested_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = PaymentAttemptStatus.PROCESSING
    kwargs["processing_started_at"] = now + timedelta(seconds=1)
    return kwargs


def _base_approved_kwargs():
    kwargs = _base_processing_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = PaymentAttemptStatus.APPROVED
    kwargs["approved_at"] = now + timedelta(seconds=2)
    kwargs["processed_at"] = now + timedelta(seconds=2)
    return kwargs


def _base_refused_kwargs():
    kwargs = _base_processing_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = PaymentAttemptStatus.REFUSED
    kwargs["refused_at"] = now + timedelta(seconds=2)
    kwargs["processed_at"] = now + timedelta(seconds=2)
    return kwargs


# ─── Criação ─────────────────────────────────────────────────────────────────
class TestPaymentAttemptCreation:
    def test_creates_with_requested_status(self):
        pa = PaymentAttempt(**_base_requested_kwargs())
        assert pa.status == PaymentAttemptStatus.REQUESTED.value

    def test_accepts_status_as_string(self):
        kwargs = _base_requested_kwargs()
        kwargs["status"] = "REQUESTED"
        pa = PaymentAttempt(**kwargs)
        assert pa.status == "REQUESTED"

    def test_requested_at_defaults_to_now_if_not_provided(self):
        kwargs = _base_requested_kwargs()
        kwargs.pop("requested_at")
        pa = PaymentAttempt(**kwargs)
        assert isinstance(pa.requested_at, datetime)

    def test_optional_fields_default_none(self):
        pa = PaymentAttempt(**_base_requested_kwargs())
        assert pa.processing_started_at is None
        assert pa.processed_at is None
        assert pa.approved_at is None
        assert pa.refused_at is None
        assert pa.provider is None
        assert pa.external_reference is None
        assert pa.refusal_reason is None
        assert pa.provider_message is None

    def test_accepts_all_optional_fields(self):
        kwargs = _base_requested_kwargs()
        kwargs["provider"] = "mock-provider"
        kwargs["external_reference"] = "ext-ref-123"
        kwargs["provider_message"] = "Aguardando processamento"
        pa = PaymentAttempt(**kwargs)
        assert pa.provider == "mock-provider"
        assert pa.external_reference == "ext-ref-123"
        assert pa.provider_message == "Aguardando processamento"

    def test_rejects_invalid_attempt_number_zero(self):
        kwargs = _base_requested_kwargs()
        kwargs["attempt_number"] = 0
        with pytest.raises(
            ValueError, match="attempt_number must be a positive integer"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_invalid_attempt_number_negative(self):
        kwargs = _base_requested_kwargs()
        kwargs["attempt_number"] = -1
        with pytest.raises(
            ValueError, match="attempt_number must be a positive integer"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_invalid_amount_zero(self):
        kwargs = _base_requested_kwargs()
        kwargs["amount"] = Decimal("0")
        with pytest.raises(ValueError, match="amount must be a positive Decimal"):
            PaymentAttempt(**kwargs)

    def test_rejects_invalid_amount_negative(self):
        kwargs = _base_requested_kwargs()
        kwargs["amount"] = Decimal("-10.00")
        with pytest.raises(ValueError, match="amount must be a positive Decimal"):
            PaymentAttempt(**kwargs)

    def test_rejects_invalid_status(self):
        kwargs = _base_requested_kwargs()
        kwargs["status"] = "INVALID_STATUS"
        with pytest.raises(ValueError, match="Invalid payment attempt status"):
            PaymentAttempt(**kwargs)


# ─── PROCESSING ──────────────────────────────────────────────────────────────


class TestPaymentAttemptProcessing:
    def test_accepts_processing_with_processing_started_at(self):
        pa = PaymentAttempt(**_base_processing_kwargs())
        assert pa.status == PaymentAttemptStatus.PROCESSING.value
        assert pa.processing_started_at is not None

    def test_rejects_processing_without_processing_started_at(self):
        kwargs = _base_processing_kwargs()
        kwargs["processing_started_at"] = None
        with pytest.raises(
            ValueError,
            match="PROCESSING payment attempt must have processing_started_at",
        ):
            PaymentAttempt(**kwargs)


# ─── APPROVED ────────────────────────────────────────────────────────────────


class TestPaymentAttemptApproved:
    def test_accepts_approved_with_approved_at(self):
        pa = PaymentAttempt(**_base_approved_kwargs())
        assert pa.status == PaymentAttemptStatus.APPROVED.value
        assert pa.approved_at is not None
        assert pa.refused_at is None

    def test_rejects_approved_without_approved_at(self):
        kwargs = _base_approved_kwargs()
        kwargs["approved_at"] = None
        with pytest.raises(
            ValueError, match="APPROVED payment attempt must have approved_at"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_approved_without_processed_at(self):
        kwargs = _base_approved_kwargs()
        kwargs["processed_at"] = None
        with pytest.raises(
            ValueError, match="APPROVED payment attempt must have processed_at"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_approved_with_refused_at(self):
        kwargs = _base_approved_kwargs()
        now = datetime.utcnow()
        kwargs["refused_at"] = now + timedelta(seconds=3)
        with pytest.raises(
            ValueError, match="APPROVED payment attempt must not have refused_at"
        ):
            PaymentAttempt(**kwargs)


# ─── REFUSED ─────────────────────────────────────────────────────────────────


class TestPaymentAttemptRefused:
    def test_accepts_refused_with_refused_at(self):
        kwargs = _base_refused_kwargs()
        kwargs["refusal_reason"] = "Saldo insuficiente"
        pa = PaymentAttempt(**kwargs)
        assert pa.status == PaymentAttemptStatus.REFUSED.value
        assert pa.refused_at is not None
        assert pa.refusal_reason == "Saldo insuficiente"

    def test_rejects_refused_without_refused_at(self):
        kwargs = _base_refused_kwargs()
        kwargs["refused_at"] = None
        with pytest.raises(
            ValueError, match="REFUSED payment attempt must have refused_at"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_refused_without_processed_at(self):
        kwargs = _base_refused_kwargs()
        kwargs["processed_at"] = None
        with pytest.raises(
            ValueError, match="REFUSED payment attempt must have processed_at"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_refused_with_approved_at(self):
        kwargs = _base_refused_kwargs()
        now = datetime.utcnow()
        kwargs["approved_at"] = now + timedelta(seconds=3)
        with pytest.raises(
            ValueError, match="REFUSED payment attempt must not have approved_at"
        ):
            PaymentAttempt(**kwargs)


# ─── Coerência temporal ──────────────────────────────────────────────────────


class TestPaymentAttemptTemporalOrder:
    def test_rejects_processing_started_before_requested(self):
        now = datetime.utcnow()
        kwargs = _base_processing_kwargs()
        kwargs["requested_at"] = now + timedelta(seconds=10)
        kwargs["processing_started_at"] = now  # antes de requested_at
        with pytest.raises(
            ValueError, match="requested_at must not be after processing_started_at"
        ):
            PaymentAttempt(**kwargs)

    def test_rejects_approved_before_processing_started(self):
        now = datetime.utcnow()
        kwargs = _base_approved_kwargs()
        kwargs["processing_started_at"] = now + timedelta(seconds=10)
        kwargs["approved_at"] = now + timedelta(seconds=5)
        kwargs["processed_at"] = now + timedelta(seconds=5)
        with pytest.raises(ValueError, match="processing_started_at must not be after"):
            PaymentAttempt(**kwargs)

    def test_rejects_refused_before_processing_started(self):
        now = datetime.utcnow()
        kwargs = _base_refused_kwargs()
        kwargs["processing_started_at"] = now + timedelta(seconds=10)
        kwargs["refused_at"] = now + timedelta(seconds=5)
        kwargs["processed_at"] = now + timedelta(seconds=5)
        with pytest.raises(ValueError, match="processing_started_at must not be after"):
            PaymentAttempt(**kwargs)


    def test_id_must_be_uuid(self):
        kw = _base_requested_kwargs()
        kw["id"] = "not-a-uuid"
        with pytest.raises(ValueError, match="ID must be a UUID"):
            PaymentAttempt(**kw)

    def test_service_request_id_must_be_uuid(self):
        kw = _base_requested_kwargs()
        kw["service_request_id"] = "not-a-uuid"
        with pytest.raises(ValueError, match="service_request_id must be a UUID"):
            PaymentAttempt(**kw)

    def test_status_in_validate_must_be_valid(self):
        """
        Cobre a verificação de status dentro de validate() (distinta do
        _normalize_status que dispara durante a atribuição).
        """
        pa = PaymentAttempt(**_base_requested_kwargs())
        pa.status = "TOTALLY_INVALID"
        with pytest.raises(ValueError, match="Invalid payment attempt status"):
            pa.validate()

    def test_requested_at_must_be_datetime(self):
        kw = _base_requested_kwargs()
        kw["requested_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="requested_at must be a datetime"):
            PaymentAttempt(**kw)

    def test_processing_started_at_must_be_datetime_or_none(self):
        kw = _base_requested_kwargs()
        kw["processing_started_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="processing_started_at must be a datetime"):
            PaymentAttempt(**kw)

    def test_processed_at_must_be_datetime_or_none(self):
        kw = _base_requested_kwargs()
        kw["processed_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="processed_at must be a datetime"):
            PaymentAttempt(**kw)

    def test_approved_at_must_be_datetime_or_none(self):
        kw = _base_requested_kwargs()
        kw["approved_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="approved_at must be a datetime"):
            PaymentAttempt(**kw)

    def test_refused_at_must_be_datetime_or_none(self):
        kw = _base_requested_kwargs()
        kw["refused_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="refused_at must be a datetime"):
            PaymentAttempt(**kw)

    def test_provider_must_be_str_or_none(self):
        kw = _base_requested_kwargs()
        kw["provider"] = 12345
        with pytest.raises(ValueError, match="provider must be a string"):
            PaymentAttempt(**kw)

    def test_external_reference_must_be_str_or_none(self):
        kw = _base_requested_kwargs()
        kw["external_reference"] = 12345
        with pytest.raises(ValueError, match="external_reference must be a string"):
            PaymentAttempt(**kw)

    def test_refusal_reason_must_be_str_or_none(self):
        kw = _base_requested_kwargs()
        kw["refusal_reason"] = 12345
        with pytest.raises(ValueError, match="refusal_reason must be a string"):
            PaymentAttempt(**kw)

    def test_provider_message_must_be_str_or_none(self):
        kw = _base_requested_kwargs()
        kw["provider_message"] = 12345
        with pytest.raises(ValueError, match="provider_message must be a string"):
            PaymentAttempt(**kw)