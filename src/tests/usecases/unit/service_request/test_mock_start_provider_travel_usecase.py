from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4
from unittest.mock import patch

from domain.notification.notification_exceptions import EmailDeliveryError
import pytest

from domain.logistics.logistics_acl_gateway_interface import (
    LogisticsAclGatewayInterface,
)
from domain.logistics.route_estimate_dto import RouteEstimateDTO
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderNotAllowedToStartTravelError,
    ServiceRequestAddressEmptyError,
    ServiceRequestDepartureAddressEmptyError,
    ServiceRequestExpiredError,
    ServiceRequestNotConfirmedError,
    ServiceRequestNotFoundError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.start_provider_travel.start_provider_travel_dto import (
    StartProviderTravelInputDTO,
    StartProviderTravelOutputDTO,
)
from usecases.service_request.start_provider_travel.start_provider_travel_usecase import (
    StartProviderTravelUseCase,
)


def _make_use_case(notification_gateway=None):
    sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    logistics = MagicMock(spec=LogisticsAclGatewayInterface)
    use_case = StartProviderTravelUseCase(
        service_request_repository=sr_repo,
        logistics_acl_gateway=logistics,
        notification_gateway=notification_gateway,
    )
    return use_case, sr_repo, logistics


def _make_confirmed_sr(
    provider_id=None,
    expires_at=None,
    departure_address="Rua Origem, 1",
    destination_address="Rua Destino, 100",
):
    sr = MagicMock()
    sr.id = uuid4()
    sr.client_id = uuid4()
    sr.accepted_provider_id = provider_id or uuid4()
    sr.status = ServiceRequestStatus.CONFIRMED.value
    sr.address = destination_address
    sr.departure_address = departure_address
    sr.expires_at = expires_at
    return sr


def _make_route_estimate(duration_minutes=25):
    now = datetime.utcnow()
    return RouteEstimateDTO(
        duration_minutes=duration_minutes,
        distance_km=Decimal("8.5"),
        estimated_arrival_at=now + timedelta(minutes=duration_minutes),
        reference="mock-ref",
    )


def _make_updated_sr(sr, route_estimate):
    updated = MagicMock()
    updated.id = sr.id
    updated.client_id = sr.client_id
    updated.status = ServiceRequestStatus.IN_TRANSIT.value
    updated.travel_started_at = datetime.utcnow()
    updated.estimated_arrival_at = route_estimate.estimated_arrival_at
    updated.travel_duration_minutes = route_estimate.duration_minutes
    updated.travel_distance_km = route_estimate.distance_km
    return updated


class TestStartProviderTravelUseCase:
    def test_success(self):
        provider_id = uuid4()
        use_case, sr_repo, logistics = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        input_dto = StartProviderTravelInputDTO(
            authenticated_user_id=provider_id,
            service_request_id=mock_sr.id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, StartProviderTravelOutputDTO)
        assert output.service_request_id == mock_sr.id
        assert output.status == ServiceRequestStatus.IN_TRANSIT.value
        assert output.travel_started_at is not None
        assert output.estimated_arrival_at == route.estimated_arrival_at
        assert output.travel_duration_minutes == route.duration_minutes
        assert output.travel_distance_km == route.distance_km

    def test_fails_if_request_not_found(self):
        use_case, sr_repo, _ = _make_use_case()
        sr_repo.find_by_id.return_value = None

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=uuid4(),
                    service_request_id=uuid4(),
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()

    def test_fails_if_provider_not_owner(self):
        provider_id = uuid4()
        other_provider_id = uuid4()
        use_case, sr_repo, _ = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=other_provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ProviderNotAllowedToStartTravelError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()

    def test_fails_if_status_not_confirmed(self):
        provider_id = uuid4()
        use_case, sr_repo, _ = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.IN_TRANSIT.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotConfirmedError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()

    def test_fails_if_expired(self):
        provider_id = uuid4()
        use_case, sr_repo, _ = _make_use_case()

        mock_sr = _make_confirmed_sr(
            provider_id=provider_id,
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestExpiredError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()

    def test_fails_if_no_departure_address(self):
        provider_id = uuid4()
        use_case, sr_repo, _ = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id, departure_address=None)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestDepartureAddressEmptyError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()

    def test_fails_if_no_destination_address(self):
        provider_id = uuid4()
        use_case, sr_repo, _ = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id, destination_address=None)
        sr_repo.find_by_id.return_value = mock_sr
        with pytest.raises(ServiceRequestAddressEmptyError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()

    def test_calls_acl_with_correct_addresses(self):
        provider_id = uuid4()
        use_case, sr_repo, logistics = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        mock_sr.departure_address = "Rua Saída, 42"
        mock_sr.address = "Rua Destino, 99"
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        call_kwargs = logistics.estimate_route.call_args.kwargs
        assert call_kwargs["origin_address"] == "Rua Saída, 42"
        assert call_kwargs["destination_address"] == "Rua Destino, 99"

    def test_fails_if_conditional_update_returns_none(self):
        provider_id = uuid4()
        use_case, sr_repo, logistics = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        sr_repo.start_travel_if_confirmed.return_value = None

        with pytest.raises(ServiceRequestNotConfirmedError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_calls_notification_after_success(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        use_case, sr_repo, logistics = _make_use_case(
            notification_gateway=notification_gateway
        )

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        notification_gateway.notify_client_travel_started.assert_called_once_with(
            client_id=updated.client_id,
            service_request_id=updated.id,
            estimated_arrival_at=updated.estimated_arrival_at,
            travel_duration_minutes=updated.travel_duration_minutes,
        )

    def test_notification_failure_does_not_rollback_transition(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        notification_gateway.notify_client_travel_started.side_effect = EmailDeliveryError("email error")
        use_case, sr_repo, logistics = _make_use_case(
            notification_gateway=notification_gateway
        )

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        # Should NOT raise despite notification failure
        output = use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, StartProviderTravelOutputDTO)
        assert output.status == ServiceRequestStatus.IN_TRANSIT.value
        notification_gateway.notify_client_travel_started.assert_called_once()

    def test_does_not_call_notification_when_not_injected(self):
        provider_id = uuid4()
        use_case, sr_repo, logistics = _make_use_case(notification_gateway=None)

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        output = use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider_id,
                service_request_id=mock_sr.id,
            )
        )

        assert isinstance(output, StartProviderTravelOutputDTO)

    def test_does_not_call_notification_when_update_fails(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        use_case, sr_repo, logistics = _make_use_case(
            notification_gateway=notification_gateway
        )

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        sr_repo.start_travel_if_confirmed.return_value = None

        with pytest.raises(ServiceRequestNotConfirmedError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        notification_gateway.notify_client_travel_started.assert_not_called()

    def test_acl_not_called_when_provider_not_owner(self):
        use_case, sr_repo, logistics = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=uuid4())
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ProviderNotAllowedToStartTravelError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=uuid4(),
                    service_request_id=mock_sr.id,
                )
            )

        logistics.estimate_route.assert_not_called()

    def test_acl_not_called_when_status_not_confirmed(self):
        provider_id = uuid4()
        use_case, sr_repo, logistics = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        mock_sr.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotConfirmedError):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        logistics.estimate_route.assert_not_called()

    def test_fails_when_logistics_acl_raises_and_does_not_update(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        use_case, sr_repo, logistics = _make_use_case(
            notification_gateway=notification_gateway
        )

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr
        logistics.estimate_route.side_effect = RuntimeError("ACL down")

        with pytest.raises(RuntimeError, match="ACL down"):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.start_travel_if_confirmed.assert_not_called()
        notification_gateway.notify_client_travel_started.assert_not_called()


    def test_passes_now_to_acl_and_repository(self):
        provider_id = uuid4()
        use_case, sr_repo, logistics = _make_use_case()

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        fixed_now = datetime(2026, 4, 8, 12, 0, 0)
        route = RouteEstimateDTO(
            duration_minutes=25,
            distance_km=Decimal("8.5"),
            estimated_arrival_at=fixed_now + timedelta(minutes=25),
            reference="mock-ref",
        )
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        with patch(
            "usecases.service_request.start_provider_travel.start_provider_travel_usecase.datetime"
        ) as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now

            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )

        logistics_kwargs = logistics.estimate_route.call_args.kwargs
        assert logistics_kwargs["departure_at"] == fixed_now

        repo_kwargs = sr_repo.start_travel_if_confirmed.call_args.kwargs
        assert repo_kwargs["now"] == fixed_now

    def test_unexpected_notification_error_is_not_swallowed(self):
        provider_id = uuid4()
        notification_gateway = MagicMock(
            spec=ServiceRequestNotificationGatewayInterface
        )
        notification_gateway.notify_client_travel_started.side_effect = TypeError("bug")

        use_case, sr_repo, logistics = _make_use_case(
            notification_gateway=notification_gateway
        )

        mock_sr = _make_confirmed_sr(provider_id=provider_id)
        sr_repo.find_by_id.return_value = mock_sr

        route = _make_route_estimate()
        logistics.estimate_route.return_value = route

        updated = _make_updated_sr(mock_sr, route)
        sr_repo.start_travel_if_confirmed.return_value = updated

        with pytest.raises(TypeError, match="bug"):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider_id,
                    service_request_id=mock_sr.id,
                )
            )
