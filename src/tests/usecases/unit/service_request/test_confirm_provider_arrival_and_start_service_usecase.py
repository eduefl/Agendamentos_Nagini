from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ClientNotAllowedToConfirmProviderArrivalError,
    ServiceRequestArrivalAlreadyConfirmedError,
    ServiceRequestNotArrivedError,
    ServiceRequestNotFoundError,
    ServiceRequestProviderArrivalNotRegisteredError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.confirm_provider_arrival_and_start_service.confirm_provider_arrival_and_start_service_dto import (
    ConfirmProviderArrivalAndStartServiceInputDTO,
    ConfirmProviderArrivalAndStartServiceOutputDTO,
)
from usecases.service_request.confirm_provider_arrival_and_start_service.confirm_provider_arrival_and_start_service_usecase import (
    ConfirmProviderArrivalAndStartServiceUseCase,
)


def _make_use_case():
    sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
    use_case = ConfirmProviderArrivalAndStartServiceUseCase(
        service_request_repository=sr_repo,
    )
    return use_case, sr_repo


def _make_arrived_sr(client_id=None):
    sr = MagicMock()
    sr.id = uuid4()
    sr.client_id = client_id or uuid4()
    sr.accepted_provider_id = uuid4()
    sr.status = ServiceRequestStatus.ARRIVED.value
    sr.provider_arrived_at = datetime.utcnow() - timedelta(minutes=5)
    return sr


def _make_updated_sr(sr):
    updated = MagicMock()
    updated.id = sr.id
    updated.client_id = sr.client_id
    updated.status = ServiceRequestStatus.IN_PROGRESS.value
    now = datetime.utcnow()
    updated.client_confirmed_provider_arrival_at = now
    updated.service_started_at = now
    return updated


class TestConfirmProviderArrivalAndStartServiceUseCase:
    def test_success(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.find_by_id.return_value = mock_sr

        updated = _make_updated_sr(mock_sr)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = updated

        input_dto = ConfirmProviderArrivalAndStartServiceInputDTO(
            authenticated_user_id=client_id,
            service_request_id=mock_sr.id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, ConfirmProviderArrivalAndStartServiceOutputDTO)
        assert output.service_request_id == mock_sr.id
        assert output.status == ServiceRequestStatus.IN_PROGRESS.value
        assert output.client_confirmed_provider_arrival_at is not None
        assert output.service_started_at is not None

    def test_fails_if_request_not_found(self):
        use_case, sr_repo = _make_use_case()
        sr_repo.find_by_id.return_value = None

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=uuid4(),
                    service_request_id=uuid4(),
                )
            )

        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.assert_not_called()

    def test_fails_if_client_not_owner(self):
        client_id = uuid4()
        other_client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=other_client_id)
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ClientNotAllowedToConfirmProviderArrivalError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.assert_not_called()

    def test_fails_if_already_in_progress(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        mock_sr.status = ServiceRequestStatus.IN_PROGRESS.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestArrivalAlreadyConfirmedError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.assert_not_called()

    def test_fails_if_status_not_arrived(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        mock_sr.status = ServiceRequestStatus.CONFIRMED.value
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestNotArrivedError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.assert_not_called()

    def test_fails_if_provider_arrived_at_missing(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        mock_sr.provider_arrived_at = None
        sr_repo.find_by_id.return_value = mock_sr

        with pytest.raises(ServiceRequestProviderArrivalNotRegisteredError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.assert_not_called()

    def test_fails_if_conditional_update_returns_none_and_reclassifies_not_found(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = None
        sr_repo.find_by_id.side_effect = [mock_sr, None]

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_reclassifies_already_in_progress(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.IN_PROGRESS.value
        reread.provider_arrived_at = datetime.utcnow() - timedelta(minutes=5)
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestArrivalAlreadyConfirmedError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_reclassifies_client_changed(self):
        client_id = uuid4()
        other_client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = None

        reread = MagicMock()
        reread.client_id = other_client_id
        reread.status = ServiceRequestStatus.ARRIVED.value
        reread.provider_arrived_at = datetime.utcnow() - timedelta(minutes=5)
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ClientNotAllowedToConfirmProviderArrivalError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_reclassifies_not_arrived(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.CONFIRMED.value
        reread.provider_arrived_at = None
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotArrivedError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_provider_arrived_at_missing_on_reread(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.ARRIVED.value
        reread.provider_arrived_at = None
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestProviderArrivalNotRegisteredError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_fails_if_conditional_update_returns_none_and_status_arrived_but_arrived_at_set(self):
        # Race condition: status is still ARRIVED and provider_arrived_at is set
        # but the conditional update still missed. This should raise ServiceRequestNotArrivedError.
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = None

        reread = MagicMock()
        reread.client_id = client_id
        reread.status = ServiceRequestStatus.ARRIVED.value
        reread.provider_arrived_at = datetime.utcnow() - timedelta(minutes=5)
        sr_repo.find_by_id.side_effect = [mock_sr, reread]

        with pytest.raises(ServiceRequestNotArrivedError):
            use_case.execute(
                ConfirmProviderArrivalAndStartServiceInputDTO(
                    authenticated_user_id=client_id,
                    service_request_id=mock_sr.id,
                )
            )

    def test_sets_same_now_for_confirmation_and_service_start(self):
        client_id = uuid4()
        use_case, sr_repo = _make_use_case()

        mock_sr = _make_arrived_sr(client_id=client_id)
        sr_repo.find_by_id.return_value = mock_sr

        fixed_now = datetime.utcnow()
        updated = MagicMock()
        updated.id = mock_sr.id
        updated.client_id = client_id
        updated.status = ServiceRequestStatus.IN_PROGRESS.value
        updated.client_confirmed_provider_arrival_at = fixed_now
        updated.service_started_at = fixed_now
        sr_repo.confirm_provider_arrival_and_start_service_if_arrived.return_value = updated

        output = use_case.execute(
            ConfirmProviderArrivalAndStartServiceInputDTO(
                authenticated_user_id=client_id,
                service_request_id=mock_sr.id,
            )
        )

        assert output.client_confirmed_provider_arrival_at == output.service_started_at