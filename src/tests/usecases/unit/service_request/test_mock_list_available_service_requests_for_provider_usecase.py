from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_dto import (
    ListAvailableServiceRequestsForProviderInputDTO,
    ListAvailableServiceRequestsForProviderOutputItemDTO,
)
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_usecase import (
    ListAvailableServiceRequestsForProviderUseCase,
)


class TestListAvailableServiceRequestsForProviderUseCase:
    def test_list_available_success(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        service_request_id = uuid4()
        client_id = uuid4()
        service_id = uuid4()
        provider_service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service_request_repository.list_available_for_provider.return_value = [
            MagicMock(
                service_request_id=service_request_id,
                client_id=client_id,
                service_id=service_id,
                service_name="Limpeza Residencial",
                service_description="Limpeza completa da residência",
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                address="Rua Teste, 123",
                status="AWAITING_PROVIDER_ACCEPTANCE",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=2),
                provider_service_id=provider_service_id,
                price=Decimal("150.00"),
            )
        ]

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListAvailableServiceRequestsForProviderInputDTO(
            provider_id=provider_id
        )
        output = use_case.execute(input_dto)

        assert len(output) == 1
        assert isinstance(output[0], ListAvailableServiceRequestsForProviderOutputItemDTO)
        assert output[0].service_request_id == service_request_id
        assert output[0].client_id == client_id
        assert output[0].service_id == service_id
        assert output[0].service_name == "Limpeza Residencial"
        assert output[0].service_description == "Limpeza completa da residência"
        assert output[0].address == "Rua Teste, 123"
        assert output[0].status == "AWAITING_PROVIDER_ACCEPTANCE"
        assert output[0].provider_service_id == provider_service_id
        assert output[0].price == Decimal("150.00")

        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_service_request_repository.list_available_for_provider.assert_called_once_with(
            provider_id=provider_id
        )

    def test_list_available_user_inactive(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        mock_user = MagicMock(id=provider_id, is_active=False)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListAvailableServiceRequestsForProviderInputDTO(
            provider_id=provider_id
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_service_request_repository.list_available_for_provider.assert_not_called()

    def test_list_available_user_not_provider(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = False
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListAvailableServiceRequestsForProviderInputDTO(
            provider_id=provider_id
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_service_request_repository.list_available_for_provider.assert_not_called()

    def test_list_available_empty_when_no_matching_requests(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service_request_repository.list_available_for_provider.return_value = []

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListAvailableServiceRequestsForProviderInputDTO(
            provider_id=provider_id
        )
        output = use_case.execute(input_dto)

        assert output == []
        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_service_request_repository.list_available_for_provider.assert_called_once_with(
            provider_id=provider_id
        )

    def test_list_available_user_not_found(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(provider_id)

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListAvailableServiceRequestsForProviderInputDTO(
            provider_id=provider_id
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_service_request_repository.list_available_for_provider.assert_not_called()