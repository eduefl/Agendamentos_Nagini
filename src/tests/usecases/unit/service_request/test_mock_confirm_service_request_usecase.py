from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ProviderDoesNotServeThisRequestError,
    ServiceRequestNotFoundError,
    ServiceRequestUnavailableError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.travel.travel_price_gateway_interface import TravelPriceGatewayInterface
from usecases.service_request.confirm_service_request.confirm_service_request_dto import (
    ConfirmServiceRequestInputDTO,
    ConfirmServiceRequestOutputDTO,
)
from usecases.service_request.confirm_service_request.confirm_service_request_usecase import (
    ConfirmServiceRequestUseCase,
)


def _make_use_case():
    service_request_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    provider_service_repo = MagicMock(spec=ProviderServiceRepositoryInterface)
    travel_gateway = MagicMock(spec=TravelPriceGatewayInterface)
    use_case = ConfirmServiceRequestUseCase(
        service_request_repository=service_request_repo,
        provider_service_repository=provider_service_repo,
        travel_price_gateway=travel_gateway,
    )
    return use_case, service_request_repo, provider_service_repo, travel_gateway


def _make_available_service_request(service_id=None, expires_at=None):
    sr = MagicMock()
    sr.id = uuid4()
    sr.service_id = service_id or uuid4()
    sr.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
    sr.address = "Rua Destino, 456"
    sr.expires_at = expires_at or (datetime.utcnow() + timedelta(hours=1))
    return sr


def _make_confirmed_service_request(service_request_id, provider_id, service_price, travel_price, total_price, accepted_at):
    confirmed = MagicMock()
    confirmed.id = service_request_id
    confirmed.status = ServiceRequestStatus.CONFIRMED.value
    confirmed.accepted_provider_id = provider_id
    confirmed.service_price = service_price
    confirmed.travel_price = travel_price
    confirmed.total_price = total_price
    confirmed.accepted_at = accepted_at
    return confirmed


class TestConfirmServiceRequestUseCase:
    def test_success(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        provider_id = uuid4()
        service_id = uuid4()
        sr_id = uuid4()
        service_price = Decimal("100.00")
        travel_price = Decimal("25.00")
        total_price = Decimal("125.00")
        accepted_at = datetime.utcnow()

        mock_sr = _make_available_service_request(service_id=service_id)
        mock_sr.id = sr_id
        sr_repo.find_by_id.return_value = mock_sr

        mock_ps = MagicMock()
        mock_ps.price = service_price
        ps_repo.find_active_by_provider_and_service.return_value = mock_ps

        travel.calculate_price.return_value = travel_price

        confirmed = _make_confirmed_service_request(sr_id, provider_id, service_price, travel_price, total_price, accepted_at)
        sr_repo.confirm_if_available.return_value = confirmed

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=sr_id,
            provider_id=provider_id,
            departure_address="Rua Saída, 123",
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, ConfirmServiceRequestOutputDTO)
        assert output.service_request_id == sr_id
        assert output.status == ServiceRequestStatus.CONFIRMED.value
        assert output.accepted_provider_id == provider_id
        assert output.service_price == service_price
        assert output.travel_price == travel_price
        assert output.total_price == total_price

        sr_repo.find_by_id.assert_called_once_with(sr_id)
        ps_repo.find_active_by_provider_and_service.assert_called_once_with(
            provider_id=provider_id,
            service_id=service_id,
        )
        travel.calculate_price.assert_called_once_with(
            departure_address="Rua Saída, 123",
            destination_address=mock_sr.address,
        )
        sr_repo.confirm_if_available.assert_called_once()

    def test_fails_if_service_request_not_found(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        sr_repo.find_by_id.return_value = None

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=uuid4(),
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(input_dto)

        ps_repo.find_active_by_provider_and_service.assert_not_called()
        sr_repo.confirm_if_available.assert_not_called()

    def test_fails_if_request_not_awaiting_acceptance(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        mock_sr = _make_available_service_request()
        mock_sr.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.return_value = mock_sr

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=mock_sr.id,
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestUnavailableError):
            use_case.execute(input_dto)

        ps_repo.find_active_by_provider_and_service.assert_not_called()

    def test_fails_if_request_expired(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        mock_sr = _make_available_service_request(
            expires_at=datetime.utcnow() - timedelta(minutes=1)
        )
        sr_repo.find_by_id.return_value = mock_sr

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=mock_sr.id,
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestUnavailableError):
            use_case.execute(input_dto)

        ps_repo.find_active_by_provider_and_service.assert_not_called()

    def test_fails_if_provider_does_not_serve_service(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        mock_sr = _make_available_service_request()
        sr_repo.find_by_id.return_value = mock_sr

        ps_repo.find_active_by_provider_and_service.return_value = None

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=mock_sr.id,
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ProviderDoesNotServeThisRequestError):
            use_case.execute(input_dto)

        sr_repo.confirm_if_available.assert_not_called()

    def test_fails_if_another_provider_already_accepted(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        mock_sr = _make_available_service_request()
        sr_repo.find_by_id.return_value = mock_sr

        mock_ps = MagicMock()
        mock_ps.price = Decimal("80.00")
        ps_repo.find_active_by_provider_and_service.return_value = mock_ps
        travel.calculate_price.return_value = Decimal("20.00")

        # confirm_if_available returns None → concurrency lost
        sr_repo.confirm_if_available.return_value = None

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=mock_sr.id,
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestUnavailableError):
            use_case.execute(input_dto)

    def test_persists_prices_correctly(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        provider_id = uuid4()
        service_id = uuid4()
        sr_id = uuid4()
        service_price = Decimal("150.00")
        travel_price = Decimal("30.00")
        total_price = service_price + travel_price

        mock_sr = _make_available_service_request(service_id=service_id)
        mock_sr.id = sr_id
        sr_repo.find_by_id.return_value = mock_sr

        mock_ps = MagicMock()
        mock_ps.price = service_price
        ps_repo.find_active_by_provider_and_service.return_value = mock_ps
        travel.calculate_price.return_value = travel_price

        confirmed = _make_confirmed_service_request(
            sr_id, provider_id, service_price, travel_price, total_price, datetime.utcnow()
        )
        sr_repo.confirm_if_available.return_value = confirmed

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=sr_id,
            provider_id=provider_id,
            departure_address="Rua Saída, 100",
        )

        output = use_case.execute(input_dto)

        assert output.service_price == service_price
        assert output.travel_price == travel_price
        assert output.total_price == total_price

        call_kwargs = sr_repo.confirm_if_available.call_args.kwargs
        assert call_kwargs["service_price"] == service_price
        assert call_kwargs["travel_price"] == travel_price
        assert call_kwargs["total_price"] == service_price + travel_price

    def test_total_equals_service_plus_travel(self):
        use_case, sr_repo, ps_repo, travel = _make_use_case()

        service_price = Decimal("200.00")
        travel_price = Decimal("45.50")
        expected_total = service_price + travel_price

        mock_sr = _make_available_service_request()
        sr_repo.find_by_id.return_value = mock_sr

        mock_ps = MagicMock()
        mock_ps.price = service_price
        ps_repo.find_active_by_provider_and_service.return_value = mock_ps
        travel.calculate_price.return_value = travel_price

        confirmed = _make_confirmed_service_request(
            mock_sr.id, uuid4(), service_price, travel_price, expected_total, datetime.utcnow()
        )
        sr_repo.confirm_if_available.return_value = confirmed

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=mock_sr.id,
            provider_id=uuid4(),
            departure_address="Rua X, 1",
        )

        output = use_case.execute(input_dto)
        assert output.total_price == expected_total