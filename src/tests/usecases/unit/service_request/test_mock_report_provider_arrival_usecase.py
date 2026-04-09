from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderNotAllowedToReportArrivalError,
    ServiceRequestArrivalAlreadyReportedError,
    ServiceRequestNotFoundError,
    ServiceRequestNotInTransitError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.report_provider_arrival.report_provider_arrival_dto import (
    ReportProviderArrivalInputDTO,
    ReportProviderArrivalOutputDTO,
)
from usecases.service_request.report_provider_arrival.report_provider_arrival_usecase import (
    ReportProviderArrivalUseCase,
)


def _make_use_case(notification_gateway=None):
    sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    use_case = ReportProviderArrivalUseCase(
        service_request_repository=sr_repo,
        notification_gateway=notification_gateway,
    )
    return use_case, sr_repo


def _make_in_transit_sr(provider_id=None):
    sr = MagicMock()
    sr.id = uuid4()
    sr.client_id = uuid4()
    sr.accepted_provider_id = provider_id or uuid4()
    sr.status = ServiceRequestStatus.IN_TRANSIT.value
    sr.travel_started_at = datetime.utcnow() - timedelta(minutes=10)
    return sr


def _make_updated_sr(sr):
    updated = MagicMock()
    updated.id = sr.id
    updated.client_id = sr.client_id
    updated.status = ServiceRequestStatus.ARRIVED.value
    updated.provider_arrived_at = datetime.utcnow()
    return updated


class TestReportProviderArrivalUseCase:
    def test_success(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr)
        sr_repo.mark_arrived_if_in_transit.return_value = updated

        input_dto = ReportProviderArrivalInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, ReportProviderArrivalOutputDTO)
        assert output.service_request_id == mock_sr.id
        assert output.status == ServiceRequestStatus.ARRIVED.value
        assert output.provider_arrived_at is not None

    def test_fails_if_request_not_found(self):
        use_case, sr_repo = _make_use_case()
        sr_repo.find_by_id.return_value = None

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=uuid4(),
                    service_request_id=uuid4(),
                )
            )

        sr_repo.mark_arrived_if_in_transit.assert_not_called()

    def test_fails_if_provider_not_owner(self):
        provider_id = uuid4()
        other_provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=other_provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ProviderNotAllowedToReportArrivalError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.mark_arrived_if_in_transit.assert_not_called()

    def test_fails_if_status_not_in_transit(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotInTransitError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.mark_arrived_if_in_transit.assert_not_called()

    def test_fails_if_already_arrived(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.ARRIVED.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestArrivalAlreadyReportedError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.mark_arrived_if_in_transit.assert_not_called()

    def test_fails_if_already_in_progress(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.IN_PROGRESS.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestArrivalAlreadyReportedError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.mark_arrived_if_in_transit.assert_not_called()

    def test_fails_if_conditional_update_returns_none_and_reclassifies_not_in_transit(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr
        sr_repo.mark_arrived_if_in_transit.return_value = None

        # On re-read: same SR but already CONFIRMED (not in transit anymore)
        reread = MagicMock()
        reread.accepted_provider_id = provider_id
        reread.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotInTransitError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_reclassifies_arrived(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.mark_arrived_if_in_transit.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = provider_id
        reread.status = ServiceRequestStatus.ARRIVED.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestArrivalAlreadyReportedError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_request_disappeared(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.mark_arrived_if_in_transit.return_value = None
        sr_repo.find_by_id.side_effect = [mock_sr, None]

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_provider_changed(self):
        provider_id = uuid4()
        other_provider_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.mark_arrived_if_in_transit.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = other_provider_id
        reread.status = ServiceRequestStatus.IN_TRANSIT.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ProviderNotAllowedToReportArrivalError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_calls_notification_after_success(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr)
        sr_repo.mark_arrived_if_in_transit.return_value = updated

        use_case.execute(
            ReportProviderArrivalInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        notification_gateway.notify_client_provider_arrived.assert_called_once_with(
            client_id=updated.client_id,
            service_request_id=updated.id,
            provider_arrived_at=updated.provider_arrived_at,
        )

    def test_notification_failure_does_not_rollback_transition(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        notification_gateway.notify_client_provider_arrived.side_effect = EmailDeliveryError(
            "email error"
        )
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr)
        sr_repo.mark_arrived_if_in_transit.return_value = updated

        output = use_case.execute(
            ReportProviderArrivalInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, ReportProviderArrivalOutputDTO)
        assert output.status == ServiceRequestStatus.ARRIVED.value
        notification_gateway.notify_client_provider_arrived.assert_called_once()

    def test_unexpected_notification_error_is_not_swallowed(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        notification_gateway.notify_client_provider_arrived.side_effect = TypeError("bug")

        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr)
        sr_repo.mark_arrived_if_in_transit.return_value = updated

        with pytest.raises(TypeError, match="bug"):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_does_not_call_notification_when_not_injected(self):
        provider_id = uuid4()
        use_case, sr_repo = _make_use_case(notification_gateway=None)

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr)
        sr_repo.mark_arrived_if_in_transit.return_value = updated

        output = use_case.execute(
            ReportProviderArrivalInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, ReportProviderArrivalOutputDTO)

    def test_does_not_call_notification_when_update_fails(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        use_case, sr_repo = _make_use_case(notification_gateway=notification_gateway)

        mock_sr = _make_in_transit_sr(provider_id=provider_id)
        sr_repo.mark_arrived_if_in_transit.return_value = None

        reread = MagicMock()
        reread.accepted_provider_id = provider_id
        reread.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotInTransitError):
            use_case.execute(
                ReportProviderArrivalInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        notification_gateway.notify_client_provider_arrived.assert_not_called()