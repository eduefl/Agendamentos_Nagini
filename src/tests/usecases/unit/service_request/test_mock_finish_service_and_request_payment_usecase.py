from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderNotAllowedToFinishServiceError,
    ServiceRequestAlreadyFinishedError,
    ServiceRequestInvalidFinalAmountError,
    ServiceRequestNotFoundError,
    ServiceRequestNotInProgressError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.finish_service_and_request_payment.finish_service_and_request_payment_dto import (
    FinishServiceAndRequestPaymentInputDTO,
    FinishServiceAndRequestPaymentOutputDTO,
)
from usecases.service_request.finish_service_and_request_payment.finish_service_and_request_payment_usecase import (
    FinishServiceAndRequestPaymentUseCase,
)


def _make_use_case(notification_gateway=None):
    sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    use_case = FinishServiceAndRequestPaymentUseCase(
        service_request_repository=sr_repo,
        notification_gateway=notification_gateway,
    )
    return use_case, sr_repo


def _make_in_progress_sr(provider_id=None, total_price=None):
    sr = MagicMock()
    sr.id = uuid4()
    sr.client_id = uuid4()
    sr.accepted_provider_id = provider_id or uuid4()
    sr.status = ServiceRequestStatus.IN_PROGRESS.value
    sr.total_price = total_price if total_price is not None else Decimal("150.00")
    sr.payment_amount = None
    sr.service_finished_at = None
    return sr


def _make_updated_sr(sr, payment_amount):
    updated = MagicMock()
    updated.id = sr.id
    updated.client_id = sr.client_id
    updated.status = ServiceRequestStatus.AWAITING_PAYMENT.value
    updated.service_finished_at = datetime.utcnow()
    updated.payment_requested_at = datetime.utcnow()
    updated.payment_amount = payment_amount
    updated.payment_last_status = PaymentStatusSnapshot.REQUESTED.value
    return updated


class TestFinishServiceAndRequestPaymentUseCase:
    def test_success(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, mock_sr.total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, FinishServiceAndRequestPaymentOutputDTO)
        assert output.service_request_id == mock_sr.id
        assert output.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert output.service_finished_at is not None
        assert output.payment_requested_at is not None
        assert output.payment_amount == mock_sr.total_price
        assert output.payment_last_status == PaymentStatusSnapshot.REQUESTED.value

    def test_creates_payment_attempt_in_requested_status(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, mock_sr.total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        use_case.execute(input_dto)

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_called_once()
        call_kwargs = sr_repo.finish_service_and_open_payment_if_in_progress.call_args[1]
        assert call_kwargs["service_request_id"] == mock_sr.id
        assert call_kwargs["provider_id"] == provider_id
        assert call_kwargs["payment_amount"] == mock_sr.total_price
        assert call_kwargs["payment_attempt_id"] is not None

    def test_materializes_payment_amount_from_total_price(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        total_price = Decimal("200.00")
        mock_sr = _make_in_progress_sr(provider_id=provider_id, total_price=total_price)
        mock_sr.payment_amount = None
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        use_case.execute(input_dto)

        call_kwargs = sr_repo.finish_service_and_open_payment_if_in_progress.call_args[1]
        assert call_kwargs["payment_amount"] == total_price

    def test_uses_existing_payment_amount_when_already_set(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.payment_amount = Decimal("180.00")
        mock_sr.total_price = Decimal("200.00")
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, Decimal("180.00"))
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        use_case.execute(input_dto)

        call_kwargs = sr_repo.finish_service_and_open_payment_if_in_progress.call_args[1]
        assert call_kwargs["payment_amount"] == Decimal("180.00")

    def test_calls_notification_with_persisted_values(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, mock_sr.total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        use_case.execute(input_dto)

        notification_gateway.notify_payment_requested.assert_called_once()
        call_kwargs = notification_gateway.notify_payment_requested.call_args[1]
        assert call_kwargs["client_id"] == updated.client_id
        assert call_kwargs["service_request_id"] == updated.id
        assert call_kwargs["payment_amount"] == updated.payment_amount
        assert call_kwargs["payment_requested_at"] == updated.payment_requested_at

    def test_notification_failure_does_not_rollback_transition(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        notification_gateway.notify_payment_requested.side_effect = EmailDeliveryError(
            "email error"
        )
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, mock_sr.total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, FinishServiceAndRequestPaymentOutputDTO)
        assert output.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        notification_gateway.notify_payment_requested.assert_called_once()

    def test_any_notification_exception_does_not_rollback_transition(self):
        """Qualquer exceção na etapa de notificação (não só EmailDeliveryError) é capturada
        em best effort — a transição AWAITING_PAYMENT é mantida e não gera 500."""
        provider_id = uuid4()
        notification_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        notification_gateway.notify_payment_requested.side_effect = RuntimeError(
            "gateway inesperado"
        )
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, mock_sr.total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        output = use_case.execute(
            FinishServiceAndRequestPaymentInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, FinishServiceAndRequestPaymentOutputDTO)
        assert output.status == ServiceRequestStatus.AWAITING_PAYMENT.value

    def test_fails_if_request_not_found(self):
        use_case, sr_repo = _make_use_case()
        sr_repo.find_by_id.return_value = None

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=uuid4(),
                    service_request_id=uuid4(),
                )
            )

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_not_called()

    def test_fails_if_provider_not_owner(self):
        provider_id = uuid4()
        other_provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=other_provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ProviderNotAllowedToFinishServiceError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_not_called()

    def test_fails_if_status_not_in_progress(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotInProgressError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_not_called()

    def test_fails_if_already_in_awaiting_payment(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.AWAITING_PAYMENT.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestAlreadyFinishedError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_not_called()

    def test_fails_if_already_completed(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.COMPLETED.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestAlreadyFinishedError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_service_finished_at_already_set(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.service_finished_at = datetime.utcnow() - timedelta(minutes=1)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestAlreadyFinishedError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_not_called()

    def test_fails_if_total_price_is_none(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.total_price = None
        mock_sr.payment_amount = None
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestInvalidFinalAmountError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.finish_service_and_open_payment_if_in_progress.assert_not_called()

    def test_fails_if_total_price_is_zero(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        mock_sr.total_price = Decimal("0")
        mock_sr.payment_amount = None
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestInvalidFinalAmountError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_reclassifies_already_finished(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = provider_id
        reread.status = ServiceRequestStatus.AWAITING_PAYMENT.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestAlreadyFinishedError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_request_disappeared(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = None
        sr_repo.find_by_id.side_effect = [mock_sr, None]

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_provider_changed(self):
        provider_id = uuid4()
        other_provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = other_provider_id
        reread.status = ServiceRequestStatus.IN_PROGRESS.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ProviderNotAllowedToFinishServiceError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_status_not_in_progress(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = provider_id
        reread.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotInProgressError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_does_not_call_notification_when_not_injected(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case(notification_gateway=None)

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr, mock_sr.total_price)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = updated

        output = use_case.execute(
            FinishServiceAndRequestPaymentInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, FinishServiceAndRequestPaymentOutputDTO)

    def test_does_not_call_notification_when_update_fails(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_progress_sr(provider_id=provider_id)
        sr_repo.finish_service_and_open_payment_if_in_progress.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = provider_id
        reread.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotInProgressError):
            use_case.execute(
                FinishServiceAndRequestPaymentInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        notification_gateway.notify_payment_requested.assert_not_called()