from unittest.mock import MagicMock
from uuid import uuid4
from domain.user.user_exceptions import UserNotFoundError
import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service_request.list_my_service_requests.list_my_service_requests_usecase import (
    ListMyServiceRequestsUseCase,
)
from usecases.service_request.list_my_service_requests.list_my_service_requests_dto import (
    ListMyServiceRequestsInputDTO,
    ListMyServiceRequestsOutputItemDTO,
)


class TestListMyServiceRequestsUseCase:
    def test_list_my_service_requests_success(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        client_id = uuid4()
        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service_request_repository.list_by_client_id_with_service_data.return_value = [
            MagicMock(
                service_request_id=uuid4(),
                client_id=client_id,
                service_id=uuid4(),
                service_name="Test Service",
                service_description="Test Description",
                desired_datetime="2023-10-01T10:00:00",
                status="REQUESTED",
                address="123 Test St",
                created_at="2023-09-01T10:00:00",
                accepted_provider_id=None,
                service_price=None,
                travel_price=None,
                total_price=None,                
                travel_started_at=None,
                estimated_arrival_at=None,
                travel_duration_minutes=None,
                travel_distance_km=None,
                provider_arrived_at=None,
                service_started_at=None,                
            )
        ]

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client_id)
        output = use_case.execute(input_dto)

        assert len(output) == 1
        assert isinstance(output[0], ListMyServiceRequestsOutputItemDTO)
        assert output[0].service_name == "Test Service"
        assert output[0].status == "REQUESTED"

        mock_user_repository.find_user_by_id.assert_called_once_with(client_id)
        mock_service_request_repository.list_by_client_id_with_service_data.assert_called_once_with(
            client_id=client_id
        )

    def test_list_my_service_requests_user_inactive(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        client_id = uuid4()
        mock_user = MagicMock(id=client_id, is_active=False)
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client_id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_service_request_repository.list_by_client_id_with_service_data.assert_not_called()

    def test_list_my_service_requests_user_not_client(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        client_id = uuid4()
        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = False
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client_id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_service_request_repository.list_by_client_id_with_service_data.assert_not_called()
        
    def test_list_my_service_requests_no_requests(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        client_id = uuid4()
        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service_request_repository.list_by_client_id_with_service_data.return_value = []

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client_id)
        output = use_case.execute(input_dto)

        assert output == []
        mock_service_request_repository.list_by_client_id_with_service_data.assert_called_once_with( client_id=client_id)

    def test_list_my_service_requests_user_not_found(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        client_id = uuid4()
        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(client_id)

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client_id)

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_service_request_repository.list_by_client_id_with_service_data.assert_not_called()
