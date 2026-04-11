"""
Testes unitários (mocks) do ConfirmPaymentUseCase — Fase 3 (rev 2).
Cobre:
- sucesso quando request está em AWAITING_PAYMENT e cliente é o dono
- falha se request não existe
- falha se usuário não é o cliente dono
- falha se status não está em AWAITING_PAYMENT
- falha se status já é PAYMENT_PROCESSING
- falha se status já é COMPLETED (erro semântico distinto)
- falha se service_finished_at é nulo
- falha se payment_requested_at é nulo
- falha se payment_amount é inválido
- falha se PaymentAttempt não existe
- falha se PaymentAttempt não está em REQUESTED
- marca ServiceRequest e PaymentAttempt atomicamente (método combinado)
- chama ACL com os parâmetros corretos somente após o banco refletir PAYMENT_PROCESSING
- delega resultado para ApplyPaymentResultUseCase
- ACL é chamada com external_reference único
- falha técnica da ACL não produz aprovação (ApplyPaymentResultUseCase recebe o erro)
- update condicional falha: re-classifica erro corretamente
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.payment.payment_acl_gateway_interface import PaymentAclGatewayInterface
from domain.payment.payment_attempt_repository_interface import (
    PaymentAttemptRepositoryInterface,
)
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_dto import PaymentResultDTO
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ClientNotAllowedToConfirmPaymentError,
    ServiceRequestAlreadyCompletedError,
    ServiceRequestNotFoundError,
    ServiceRequestNotAwaitingPaymentError,
    ServiceRequestPaymentAlreadyProcessingError,
    ServiceRequestPaymentAmountInvalidError,
    ServiceRequestPaymentNotRequestedError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.apply_payment_result.apply_payment_result_usecase import (
    ApplyPaymentResultUseCase,
)
from usecases.service_request.confirm_payment.confirm_payment_dto import (
    ConfirmPaymentInputDTO,
    ConfirmPaymentOutputDTO,
)
from usecases.service_request.confirm_payment.confirm_payment_usecase import (
    ConfirmPaymentUseCase,
)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_use_case():
    sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    pa_repo = MagicMock(spec=PaymentAttemptRepositoryInterface)
    acl = MagicMock(spec=PaymentAclGatewayInterface)
    apply_uc = MagicMock(spec=ApplyPaymentResultUseCase)
    use_case = ConfirmPaymentUseCase(
        service_request_repository=sr_repo,
        payment_attempt_repository=pa_repo,
        payment_acl_gateway=acl,
        apply_payment_result_usecase=apply_uc,
    )
    return use_case, sr_repo, pa_repo, acl, apply_uc


def _make_awaiting_payment_sr(client_id=None):
    sr = MagicMock()
    sr.id = uuid4()
    sr.client_id = client_id or uuid4()
    sr.status = ServiceRequestStatus.AWAITING_PAYMENT.value
    sr.service_finished_at = datetime.utcnow() - timedelta(minutes=5)
    sr.payment_requested_at = datetime.utcnow() - timedelta(minutes=5)
    sr.payment_amount = Decimal("150.00")
    return sr


def _make_requested_attempt(service_request_id=None):
    attempt = MagicMock()
    attempt.id = uuid4()
    attempt.service_request_id = service_request_id or uuid4()
    attempt.attempt_number = 1
    attempt.amount = Decimal("150.00")
    attempt.status = PaymentAttemptStatus.REQUESTED.value
    attempt.requested_at = datetime.utcnow() - timedelta(minutes=5)
    return attempt


def _make_updated_sr(sr):
    updated = MagicMock()
    updated.id = sr.id
    updated.client_id = sr.client_id
    updated.status = ServiceRequestStatus.PAYMENT_PROCESSING.value
    updated.payment_processing_started_at = datetime.utcnow()
    updated.payment_amount = sr.payment_amount
    updated.payment_requested_at = sr.payment_requested_at
    updated.payment_reference = None
    updated.payment_provider = None
    return updated


def _make_acl_result(external_reference=None):
    return PaymentResultDTO(
        provider="mock-payment-provider",
        external_reference=external_reference or str(uuid4()),
        status=PaymentAttemptStatus.APPROVED,
        processed_at=datetime.utcnow(),
        provider_message="Aprovado",
    )


def _setup_success(sr_repo, pa_repo, acl, client_id=None):
    """Sets up mocks for the happy path; returns (mock_sr, attempt, updated, acl_result)."""
    client_id = client_id or uuid4()
    mock_sr = _make_awaiting_payment_sr(client_id=client_id)
    sr_repo.find_by_id.return_value = mock_sr

    attempt = _make_requested_attempt(service_request_id=mock_sr.id)
    pa_repo.find_latest_by_service_request_id.return_value = attempt

    updated = _make_updated_sr(mock_sr)
    sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = updated

    acl_result = _make_acl_result()
    acl.process_payment.return_value = acl_result
    return client_id, mock_sr, attempt, updated, acl_result


# ─── testes ──────────────────────────────────────────────────────────────────

class TestConfirmPaymentUseCase:

    def test_success(self):
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        client_id, mock_sr, attempt, updated, acl_result = _setup_success(sr_repo, pa_repo, acl)

        output = use_case.execute(
            ConfirmPaymentInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, ConfirmPaymentOutputDTO)
        assert output.service_request_id == mock_sr.id
        assert output.status == ServiceRequestStatus.PAYMENT_PROCESSING.value
        assert output.payment_processing_started_at is not None
        assert output.payment_reference == acl_result.external_reference

    def test_uses_combined_atomic_method(self):
        """A transição atômica de SR+Attempt deve usar o método combinado."""
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        client_id, mock_sr, attempt, updated, acl_result = _setup_success(sr_repo, pa_repo, acl)

        use_case.execute(
            ConfirmPaymentInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_called_once()
        call_kwargs = sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.call_args[1]
        assert call_kwargs["service_request_id"] == mock_sr.id
        assert call_kwargs["client_id"] == client_id
        assert call_kwargs["attempt_id"] == attempt.id
        assert isinstance(call_kwargs["now"], datetime)

    def test_separate_mark_processing_not_called(self):
        """mark_processing individual NÃO deve ser chamado — a atomicidade é feita pelo repo."""
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        client_id, mock_sr, attempt, updated, acl_result = _setup_success(sr_repo, pa_repo, acl)

        use_case.execute(
            ConfirmPaymentInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        pa_repo.mark_processing.assert_not_called()

    def test_acl_called_only_after_atomic_commit(self):
        """ACL só é chamada depois que start_payment_processing_and_mark_attempt retorna."""
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        call_order = []

        client_id, mock_sr, attempt, updated, acl_result = _setup_success(sr_repo, pa_repo, acl)

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.side_effect = (
            lambda **kw: (call_order.append("atomic_update"), updated)[1]
        )
        acl.process_payment.side_effect = (
            lambda **kw: (call_order.append("acl_call"), acl_result)[1]
        )

        use_case.execute(
            ConfirmPaymentInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        assert call_order == ["atomic_update", "acl_call"]

    def test_calls_acl_with_correct_params(self):
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        client_id, mock_sr, attempt, updated, acl_result = _setup_success(sr_repo, pa_repo, acl)

        use_case.execute(
            ConfirmPaymentInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        acl.process_payment.assert_called_once()
        call_kwargs = acl.process_payment.call_args[1]
        assert call_kwargs["amount"] == updated.payment_amount
        assert call_kwargs["payer_id"] == updated.client_id
        assert call_kwargs["service_request_id"] == updated.id
        assert call_kwargs["external_reference"] is not None

    def test_delegates_result_to_apply_payment_result_usecase(self):
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        client_id, mock_sr, attempt, updated, acl_result = _setup_success(sr_repo, pa_repo, acl)

        use_case.execute(
            ConfirmPaymentInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        apply_uc.execute.assert_called_once()
        call_kwargs = apply_uc.execute.call_args[1]
        assert call_kwargs["service_request_id"] == updated.id
        assert call_kwargs["attempt_id"] == attempt.id
        assert call_kwargs["payment_result"] == acl_result

    def test_acl_technical_failure_does_not_mark_as_approved(self):
        """Falha técnica da ACL não deve produzir aprovação indevida."""
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        client_id, mock_sr, attempt, updated, _ = _setup_success(sr_repo, pa_repo, acl)

        acl.process_payment.side_effect = RuntimeError("gateway timeout")

        with pytest.raises(RuntimeError, match="gateway timeout"):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        apply_uc.execute.assert_not_called()

    def test_fails_if_request_not_found(self):
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()
        sr_repo.find_by_id.return_value = None

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=uuid4(),
                    service_request_id=uuid4(),
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_user_not_client_owner(self):
        client_id = uuid4()
        other_client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=other_client_id)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ClientNotAllowedToConfirmPaymentError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_status_not_awaiting_payment(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.status = ServiceRequestStatus.IN_PROGRESS.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotAwaitingPaymentError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_already_payment_processing(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.status = ServiceRequestStatus.PAYMENT_PROCESSING.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestPaymentAlreadyProcessingError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_already_completed_with_completed_error(self):
        """COMPLETED deve levantar ServiceRequestAlreadyCompletedError"""
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.status = ServiceRequestStatus.COMPLETED.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestAlreadyCompletedError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_service_finished_at_is_none(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.service_finished_at = None
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotAwaitingPaymentError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_payment_requested_at_is_none(self):
        """payment_requested_at é pré-condição explícita do refinamento."""
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.payment_requested_at = None
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotAwaitingPaymentError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_payment_amount_is_none(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.payment_amount = None
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestPaymentAmountInvalidError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_payment_amount_is_zero(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        mock_sr.payment_amount = Decimal("0")
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestPaymentAmountInvalidError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_no_payment_attempt_exists(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        sr_repo.find_by_id.return_value = mock_sr
        pa_repo.find_latest_by_service_request_id.return_value = None

        with pytest.raises(ServiceRequestPaymentNotRequestedError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_fails_if_attempt_not_in_requested_status(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        sr_repo.find_by_id.return_value = mock_sr

        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        attempt.status = PaymentAttemptStatus.PROCESSING.value
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        with pytest.raises(ServiceRequestPaymentNotRequestedError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.assert_not_called()

    def test_propagates_payment_not_requested_from_repo(self):
        """Se o repo levanta ServiceRequestPaymentNotRequestedError (PA fora de REQUESTED),
        o use case deve propagá-la sem chamar a ACL."""
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        sr_repo.find_by_id.return_value = mock_sr

        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.side_effect = (
            ServiceRequestPaymentNotRequestedError()
        )

        with pytest.raises(ServiceRequestPaymentNotRequestedError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        acl.process_payment.assert_not_called()
        apply_uc.execute.assert_not_called()

    def test_conditional_update_failure_reclassifies_already_processing(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.PAYMENT_PROCESSING.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestPaymentAlreadyProcessingError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_conditional_update_failure_reclassifies_completed(self):
        """Quando o banco mostra COMPLETED, deve levantar ServiceRequestAlreadyCompletedError."""
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.COMPLETED.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestAlreadyCompletedError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_conditional_update_failure_reclassifies_request_disappeared(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = None
        sr_repo.find_by_id.side_effect = [mock_sr, None]

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_conditional_update_failure_reclassifies_not_client_owner(self):
        client_id = uuid4()
        other_client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = None

        reread = MagicMock()
        reread.client_id = other_client_id
        reread.status = ServiceRequestStatus.AWAITING_PAYMENT.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ClientNotAllowedToConfirmPaymentError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_conditional_update_failure_reclassifies_wrong_status(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.IN_PROGRESS.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotAwaitingPaymentError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_acl_not_called_if_transition_fails(self):
        client_id = uuid4()
        use_case, sr_repo, pa_repo, acl, apply_uc = _make_use_case()

        mock_sr = _make_awaiting_payment_sr(client_id=client_id)
        attempt = _make_requested_attempt(service_request_id=mock_sr.id)
        pa_repo.find_latest_by_service_request_id.return_value = attempt

        sr_repo.start_payment_processing_and_mark_attempt_if_awaiting_payment.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.PAYMENT_PROCESSING.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestPaymentAlreadyProcessingError):
            use_case.execute(
                ConfirmPaymentInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        acl.process_payment.assert_not_called()
        apply_uc.execute.assert_not_called()