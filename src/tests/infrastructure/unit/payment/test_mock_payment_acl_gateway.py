"""
Testes unitários do MockPaymentAclGateway.
Cobre:
- Retorna PaymentResultDTO aprovado de forma determinística (amount < 500)
- Retorna PaymentResultDTO recusado de forma determinística (amount >= 500)
- Preenche processed_at
- Preenche external_reference
- Preenche provider_message
- Não usa aleatoriedade (mesmo input -> mesmo status)
- forced_status força aprovação independente do valor
- forced_status força recusa independente do valor
- Retorna refusal_reason quando recusado
- refusal_reason é None quando aprovado
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4
import pytest
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_dto import PaymentResultDTO
from infrastructure.payment.mock.mock_payment_acl_gateway import MockPaymentAclGateway

_COMMON_ARGS = dict(
    payer_id=uuid4(),
    service_request_id=uuid4(),
    requested_at=datetime(2026, 4, 9, 10, 0, 0),
)


class TestMockPaymentAclGateway:
    def test_returns_payment_result_dto(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-001",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert isinstance(result, PaymentResultDTO)

    def test_approves_when_amount_below_500(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-002",
            amount=Decimal("499.99"),
            **_COMMON_ARGS,
        )
        assert result.status == PaymentAttemptStatus.APPROVED

    def test_refuses_when_amount_equals_500(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-003",
            amount=Decimal("500.00"),
            **_COMMON_ARGS,
        )
        assert result.status == PaymentAttemptStatus.REFUSED

    def test_refuses_when_amount_above_500(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-004",
            amount=Decimal("600.00"),
            **_COMMON_ARGS,
        )
        assert result.status == PaymentAttemptStatus.REFUSED

    def test_fills_processed_at(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-005",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert isinstance(result.processed_at, datetime)

    def test_fills_external_reference(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="my-ref-abc",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert result.external_reference == "my-ref-abc"

    def test_fills_provider_message_when_approved(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-006",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert result.provider_message is not None
        assert len(result.provider_message) > 0

    def test_fills_provider_message_when_refused(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-007",
            amount=Decimal("600.00"),
            **_COMMON_ARGS,
        )
        assert result.provider_message is not None
        assert len(result.provider_message) > 0

    def test_refusal_reason_is_none_when_approved(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-008",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert result.refusal_reason is None

    def test_refusal_reason_is_filled_when_refused(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-009",
            amount=Decimal("600.00"),
            **_COMMON_ARGS,
        )
        assert result.refusal_reason is not None
        assert len(result.refusal_reason) > 0

    def test_is_deterministic_same_amount_approved(self):
        gateway = MockPaymentAclGateway()
        args = dict(
            external_reference="ref-010", amount=Decimal("100.00"), **_COMMON_ARGS
        )
        result1 = gateway.process_payment(**args)
        result2 = gateway.process_payment(**args)
        assert result1.status == result2.status

    def test_is_deterministic_same_amount_refused(self):
        gateway = MockPaymentAclGateway()
        args = dict(
            external_reference="ref-011", amount=Decimal("600.00"), **_COMMON_ARGS
        )
        result1 = gateway.process_payment(**args)
        result2 = gateway.process_payment(**args)
        assert result1.status == result2.status

    def test_forced_status_approved_overrides_high_amount(self):
        gateway = MockPaymentAclGateway(forced_status=PaymentAttemptStatus.APPROVED)
        result = gateway.process_payment(
            external_reference="ref-012",
            amount=Decimal("999.00"),
            **_COMMON_ARGS,
        )
        assert result.status == PaymentAttemptStatus.APPROVED

    def test_forced_status_refused_overrides_low_amount(self):
        gateway = MockPaymentAclGateway(forced_status=PaymentAttemptStatus.REFUSED)
        result = gateway.process_payment(
            external_reference="ref-013",
            amount=Decimal("1.00"),
            **_COMMON_ARGS,
        )
        assert result.status == PaymentAttemptStatus.REFUSED

    def test_provider_name_is_set(self):
        gateway = MockPaymentAclGateway()
        result = gateway.process_payment(
            external_reference="ref-014",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert result.provider is not None
        assert len(result.provider) > 0

    def test_custom_provider_name(self):
        gateway = MockPaymentAclGateway(provider="custom-provider")
        result = gateway.process_payment(
            external_reference="ref-015",
            amount=Decimal("100.00"),
            **_COMMON_ARGS,
        )
        assert result.provider == "custom-provider"
