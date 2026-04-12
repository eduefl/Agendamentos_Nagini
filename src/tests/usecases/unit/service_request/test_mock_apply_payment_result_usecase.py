"""
Testes unitários (mocks) do ApplyPaymentResultUseCase — Fase 4.
Cobre:
- aprovado leva para COMPLETED
- aprovado preenche payment_approved_at e service_concluded_at via método atômico
- aprovado marca tentativa como APPROVED
- recusado volta para AWAITING_PAYMENT via método atômico
- recusado preenche payment_refused_at
- recusado não preenche service_concluded_at
- recusado marca tentativa como REFUSED
- persiste refusal_reason
- status inválido (nem APPROVED nem REFUSED) levanta PaymentResultStatusInvalidError
- segunda aplicação do mesmo resultado retorna 409 (ServiceRequestAlreadyCompletedError)
- segunda aplicação em SR não-PAYMENT_PROCESSING retorna 409 (ServiceRequestPaymentNotProcessingError)
- falha de notificação não reverte a transição (best effort)
- notificação de aprovação é chamada após commit
- notificação de recusa é chamada após commit
- notificação não é chamada se gateway é None
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, call
from uuid import uuid4

import pytest

from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.payment.payment_attempt_repository_interface import (
    PaymentAttemptRepositoryInterface,
)
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_dto import PaymentResultDTO
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    PaymentAttemptNotProcessingError,
    PaymentResultStatusInvalidError,
    ServiceRequestAlreadyCompletedError,
    ServiceRequestNotFoundError,
    ServiceRequestPaymentNotProcessingError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.apply_payment_result.apply_payment_result_usecase import (
    ApplyPaymentResultUseCase,
)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_use_case(with_notification_gateway=False):
    sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    pa_repo = MagicMock(spec=PaymentAttemptRepositoryInterface)
    notification_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface) if with_notification_gateway else None
    use_case = ApplyPaymentResultUseCase(
        service_request_repository=sr_repo,
        payment_attempt_repository=pa_repo,
        notification_gateway=notification_gateway,
    )
    return use_case, sr_repo, pa_repo, notification_gateway


def _make_approved_result(processed_at=None):
    return PaymentResultDTO(
        provider="mock-payment-provider",
        external_reference=str(uuid4()),
        status=PaymentAttemptStatus.APPROVED,
        processed_at=processed_at or datetime.utcnow(),
        provider_message="Pagamento aprovado pelo mock",
    )


def _make_refused_result(processed_at=None):
    return PaymentResultDTO(
        provider="mock-payment-provider",
        external_reference=str(uuid4()),
        status=PaymentAttemptStatus.REFUSED,
        processed_at=processed_at or datetime.utcnow(),
        refusal_reason="Valor acima do limite permitido",
        provider_message="Pagamento recusado pelo mock",
    )


def _make_completed_sr(sr_id, client_id, provider_id, amount):
    sr = MagicMock()
    sr.id = sr_id
    sr.client_id = client_id
    sr.accepted_provider_id = provider_id
    sr.status = ServiceRequestStatus.COMPLETED.value
    sr.payment_amount = amount
    sr.payment_approved_at = datetime.utcnow()
    sr.service_concluded_at = datetime.utcnow()
    return sr


def _make_awaiting_payment_sr(sr_id, client_id, provider_id, amount):
    sr = MagicMock()
    sr.id = sr_id
    sr.client_id = client_id
    sr.accepted_provider_id = provider_id
    sr.status = ServiceRequestStatus.AWAITING_PAYMENT.value
    sr.payment_amount = amount
    sr.payment_refused_at = datetime.utcnow()
    sr.service_concluded_at = None
    return sr


# ─── testes ──────────────────────────────────────────────────────────────────

class TestApplyPaymentResultUseCaseApproved:

    def test_approved_calls_atomic_approved_method(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()
        attempt_id = uuid4()
        client_id = uuid4()
        provider_id = uuid4()
        amount = Decimal("150.00")

        result = _make_approved_result()
        completed = _make_completed_sr(sr_id, client_id, provider_id, amount)
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=attempt_id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        sr_repo.mark_payment_approved_and_complete_service_if_processing.assert_called_once_with(
            service_request_id=sr_id,
            attempt_id=attempt_id,
            provider=result.provider,
            external_reference=result.external_reference,
            provider_message=result.provider_message,
            processed_at=result.processed_at,
        )

    def test_approved_does_not_call_refused_method(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()
        attempt_id = uuid4()
        client_id = uuid4()
        provider_id = uuid4()
        amount = Decimal("150.00")

        result = _make_approved_result()
        completed = _make_completed_sr(sr_id, client_id, provider_id, amount)
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=attempt_id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.assert_not_called()

    def test_approved_uses_processed_at_from_result(self):
        """O timestamp canônico deve vir de payment_result.processed_at."""
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()
        attempt_id = uuid4()
        processed_at = datetime.utcnow() - timedelta(seconds=5)

        result = _make_approved_result(processed_at=processed_at)
        completed = _make_completed_sr(sr_id, uuid4(), uuid4(), Decimal("150.00"))
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=attempt_id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        call_kwargs = sr_repo.mark_payment_approved_and_complete_service_if_processing.call_args[1]
        assert call_kwargs["processed_at"] == processed_at

    def test_approved_raises_already_completed_on_replay(self):
        """Replay em SR já COMPLETED deve levantar ServiceRequestAlreadyCompletedError (409)."""
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()

        # Atomic method returns None (precondition not met)
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = None

        # SR is COMPLETED (replay scenario)
        completed_sr = MagicMock()
        completed_sr.status = ServiceRequestStatus.COMPLETED.value
        sr_repo.find_by_id.return_value = completed_sr

        with pytest.raises(ServiceRequestAlreadyCompletedError):
            use_case.execute(
                service_request_id=sr_id,
                attempt_id=uuid4(),
                payment_result=_make_approved_result(),
                now=datetime.utcnow(),
            )

    def test_approved_raises_not_processing_when_wrong_state(self):
        """Atomic method returning None for non-COMPLETED SR -> ServiceRequestPaymentNotProcessingError."""
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()

        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = None

        # SR is AWAITING_PAYMENT (previous refusal, calling again)
        awaiting_sr = MagicMock()
        awaiting_sr.status = ServiceRequestStatus.AWAITING_PAYMENT.value
        sr_repo.find_by_id.return_value = awaiting_sr

        with pytest.raises(ServiceRequestPaymentNotProcessingError):
            use_case.execute(
                service_request_id=sr_id,
                attempt_id=uuid4(),
                payment_result=_make_approved_result(),
                now=datetime.utcnow(),
            )

    def test_approved_raises_not_found_when_sr_disappears(self):
        """Se SR desapareceu após atomic None, levantar NotFoundError."""
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()

        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = None
        sr_repo.find_by_id.return_value = None

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                service_request_id=sr_id,
                attempt_id=uuid4(),
                payment_result=_make_approved_result(),
                now=datetime.utcnow(),
            )

    def test_approved_propagates_attempt_not_processing_error(self):
        """Se PA não está em PROCESSING, o repositório levanta PaymentAttemptNotProcessingError."""
        use_case, sr_repo, pa_repo, _ = _make_use_case()

        sr_repo.mark_payment_approved_and_complete_service_if_processing.side_effect = (
            PaymentAttemptNotProcessingError()
        )

        with pytest.raises(PaymentAttemptNotProcessingError):
            use_case.execute(
                service_request_id=uuid4(),
                attempt_id=uuid4(),
                payment_result=_make_approved_result(),
                now=datetime.utcnow(),
            )


class TestApplyPaymentResultUseCaseRefused:

    def test_refused_calls_atomic_refused_method(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()
        attempt_id = uuid4()
        client_id = uuid4()
        provider_id = uuid4()
        amount = Decimal("600.00")

        result = _make_refused_result()
        awaiting = _make_awaiting_payment_sr(sr_id, client_id, provider_id, amount)
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = awaiting

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=attempt_id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.assert_called_once_with(
            service_request_id=sr_id,
            attempt_id=attempt_id,
            provider=result.provider,
            external_reference=result.external_reference,
            refusal_reason=result.refusal_reason,
            provider_message=result.provider_message,
            processed_at=result.processed_at,
        )

    def test_refused_does_not_call_approved_method(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()
        amount = Decimal("600.00")

        result = _make_refused_result()
        awaiting = _make_awaiting_payment_sr(sr_id, uuid4(), uuid4(), amount)
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = awaiting

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        sr_repo.mark_payment_approved_and_complete_service_if_processing.assert_not_called()

    def test_refused_uses_processed_at_from_result(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()
        processed_at = datetime.utcnow() - timedelta(seconds=3)

        result = _make_refused_result(processed_at=processed_at)
        awaiting = _make_awaiting_payment_sr(sr_id, uuid4(), uuid4(), Decimal("600.00"))
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = awaiting

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        call_kwargs = sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.call_args[1]
        assert call_kwargs["processed_at"] == processed_at

    def test_refused_persists_refusal_reason(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()

        result = _make_refused_result()
        awaiting = _make_awaiting_payment_sr(sr_id, uuid4(), uuid4(), Decimal("600.00"))
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = awaiting

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        call_kwargs = sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.call_args[1]
        assert call_kwargs["refusal_reason"] == result.refusal_reason

    def test_refused_raises_not_processing_on_replay(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()
        sr_id = uuid4()

        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = None

        completed_sr = MagicMock()
        completed_sr.status = ServiceRequestStatus.COMPLETED.value
        sr_repo.find_by_id.return_value = completed_sr

        with pytest.raises(ServiceRequestAlreadyCompletedError):
            use_case.execute(
                service_request_id=sr_id,
                attempt_id=uuid4(),
                payment_result=_make_refused_result(),
                now=datetime.utcnow(),
            )

    def test_refused_propagates_attempt_not_processing_error(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()

        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.side_effect = (
            PaymentAttemptNotProcessingError()
        )

        with pytest.raises(PaymentAttemptNotProcessingError):
            use_case.execute(
                service_request_id=uuid4(),
                attempt_id=uuid4(),
                payment_result=_make_refused_result(),
                now=datetime.utcnow(),
            )


class TestApplyPaymentResultUseCaseValidation:

    def test_invalid_status_raises_payment_result_status_invalid(self):
        """Status diferente de APPROVED/REFUSED levanta PaymentResultStatusInvalidError."""
        use_case, sr_repo, pa_repo, _ = _make_use_case()

        invalid_result = PaymentResultDTO(
            provider="mock",
            external_reference=str(uuid4()),
            status=PaymentAttemptStatus.PROCESSING,  # invalid for apply
            processed_at=datetime.utcnow(),
        )

        with pytest.raises(PaymentResultStatusInvalidError):
            use_case.execute(
                service_request_id=uuid4(),
                attempt_id=uuid4(),
                payment_result=invalid_result,
                now=datetime.utcnow(),
            )

        sr_repo.mark_payment_approved_and_complete_service_if_processing.assert_not_called()
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.assert_not_called()

    def test_requested_status_raises_payment_result_status_invalid(self):
        use_case, sr_repo, pa_repo, _ = _make_use_case()

        invalid_result = PaymentResultDTO(
            provider="mock",
            external_reference=str(uuid4()),
            status=PaymentAttemptStatus.REQUESTED,
            processed_at=datetime.utcnow(),
        )

        with pytest.raises(PaymentResultStatusInvalidError):
            use_case.execute(
                service_request_id=uuid4(),
                attempt_id=uuid4(),
                payment_result=invalid_result,
                now=datetime.utcnow(),
            )


class TestApplyPaymentResultUseCaseNotifications:

    def test_approved_notifies_payment_approved_after_commit(self):
        use_case, sr_repo, pa_repo, notification_gateway = _make_use_case(with_notification_gateway=True)
        sr_id = uuid4()
        client_id = uuid4()
        provider_id = uuid4()
        amount = Decimal("150.00")

        result = _make_approved_result()
        completed = _make_completed_sr(sr_id, client_id, provider_id, amount)
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        notification_gateway.notify_payment_approved.assert_called_once()
        call_kwargs = notification_gateway.notify_payment_approved.call_args[1]
        assert call_kwargs["client_id"] == client_id
        assert call_kwargs["provider_id"] == provider_id
        assert call_kwargs["service_request_id"] == sr_id
        assert call_kwargs["payment_amount"] == amount
        assert call_kwargs["payment_approved_at"] == result.processed_at

    def test_refused_notifies_payment_refused_after_commit(self):
        use_case, sr_repo, pa_repo, notification_gateway = _make_use_case(with_notification_gateway=True)
        sr_id = uuid4()
        client_id = uuid4()
        provider_id = uuid4()
        amount = Decimal("600.00")

        result = _make_refused_result()
        awaiting = _make_awaiting_payment_sr(sr_id, client_id, provider_id, amount)
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = awaiting

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        notification_gateway.notify_payment_refused.assert_called_once()
        call_kwargs = notification_gateway.notify_payment_refused.call_args[1]
        assert call_kwargs["client_id"] == client_id
        assert call_kwargs["provider_id"] == provider_id
        assert call_kwargs["service_request_id"] == sr_id
        assert call_kwargs["payment_amount"] == amount
        assert call_kwargs["refusal_reason"] == result.refusal_reason

    def test_approved_does_not_notify_refused(self):
        use_case, sr_repo, pa_repo, notification_gateway = _make_use_case(with_notification_gateway=True)
        sr_id = uuid4()

        result = _make_approved_result()
        completed = _make_completed_sr(sr_id, uuid4(), uuid4(), Decimal("150.00"))
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        notification_gateway.notify_payment_refused.assert_not_called()

    def test_refused_does_not_notify_approved(self):
        use_case, sr_repo, pa_repo, notification_gateway = _make_use_case(with_notification_gateway=True)
        sr_id = uuid4()

        result = _make_refused_result()
        awaiting = _make_awaiting_payment_sr(sr_id, uuid4(), uuid4(), Decimal("600.00"))
        sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing.return_value = awaiting

        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        notification_gateway.notify_payment_approved.assert_not_called()

    def test_notification_failure_does_not_raise(self):
        """Falha na notificação não deve reverter a transição (best effort)."""
        from domain.notification.notification_exceptions import EmailDeliveryError

        use_case, sr_repo, pa_repo, notification_gateway = _make_use_case(with_notification_gateway=True)
        sr_id = uuid4()

        result = _make_approved_result()
        completed = _make_completed_sr(sr_id, uuid4(), uuid4(), Decimal("150.00"))
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        notification_gateway.notify_payment_approved.side_effect = EmailDeliveryError("mail down")

        # Should not raise
        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )

        # Notification was still attempted
        notification_gateway.notify_payment_approved.assert_called_once()

    def test_no_notification_when_gateway_is_none(self):
        """Sem gateway, nenhuma exceção deve ocorrer."""
        use_case, sr_repo, pa_repo, _ = _make_use_case(with_notification_gateway=False)
        sr_id = uuid4()

        result = _make_approved_result()
        completed = _make_completed_sr(sr_id, uuid4(), uuid4(), Decimal("150.00"))
        sr_repo.mark_payment_approved_and_complete_service_if_processing.return_value = completed

        # Should not raise even without notification gateway
        use_case.execute(
            service_request_id=sr_id,
            attempt_id=uuid4(),
            payment_result=result,
            now=datetime.utcnow(),
        )