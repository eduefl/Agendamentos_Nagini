from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from domain.__seedwork.exceptions import ForbiddenError
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
import pytest

from usecases.service.list_provider_services.list_provider_services_usecase import (
    ListProviderServicesUseCase,
)
from domain.user.user_repository_interface import userRepositoryInterface

from usecases.service.list_provider_services.list_provider_services_dto import (
    ListProviderServicesInputDTO,
    ListProviderServicesOutputDTO,
)
from domain.user.user_exceptions import UserNotFoundError


class TestMockListProviderServicesUseCase:
    def test_list_provider_services_success(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        mock_user_repository.find_user_by_id.return_value = MagicMock(
            id=provider_id
        )  # Simulate user found

        mock_provider_service_repository.list_by_provider_id.return_value = [
            MagicMock(
                id=uuid4(),
                provider_id=provider_id,
                service_id=uuid4(),
                price=100.0,
                active=True,
                service_name="Test Service",
                service_description="Test Description",
                created_at=datetime.utcnow(),
            ),
            MagicMock(
                id=uuid4(),
                provider_id=provider_id,
                service_id=uuid4(),
                price=150.0,
                active=True,
                service_name="Another Service",
                service_description="Test Description",
                created_at=datetime.utcnow(),
            ),
        ]

        use_case = ListProviderServicesUseCase(
            mock_provider_service_repository, mock_user_repository
        )
        output = use_case.execute(input_dto)

        assert isinstance(output, ListProviderServicesOutputDTO)
        assert len(output.items) == 2
        assert output.items[0].service_name == "Test Service"
        assert output.items[1].service_name == "Another Service"

        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_provider_service_repository.list_by_provider_id.assert_called_once_with(
            provider_id
        )

    def test_list_provider_services_user_not_found(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(
            provider_id
        )

        use_case = ListProviderServicesUseCase(
            mock_provider_service_repository, mock_user_repository
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_provider_service_repository.list_by_provider_id.assert_not_called()

    def test_list_provider_services_no_services(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        mock_user_repository.find_user_by_id.return_value = MagicMock(
            id=provider_id
        )  # Simulate user found
        mock_provider_service_repository.list_by_provider_id.return_value = (
            []
        )  # No services

        use_case = ListProviderServicesUseCase(
            mock_provider_service_repository, mock_user_repository
        )
        output = use_case.execute(input_dto)

        assert isinstance(output, ListProviderServicesOutputDTO)
        assert len(output.items) == 0  # No services should be returned

        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_provider_service_repository.list_by_provider_id.assert_called_once_with(
            provider_id
        )

    def test_list_provider_services_provider_inactive(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        mock_user_repository.find_user_by_id.return_value = MagicMock(
            id=provider_id, is_active=False
        )  # Simulate inactive user
        mock_provider_service_repository.list_by_provider_id.return_value = [
            MagicMock(
                id=uuid4(),
                provider_id=provider_id,
                service_id=uuid4(),
                price=100.0,
                active=True,
                service_name="Test Service",
                service_description="Test Description",
                created_at=datetime.utcnow(),
            )
        ]

        use_case = ListProviderServicesUseCase(
            mock_provider_service_repository, mock_user_repository
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_provider_service_repository.list_by_provider_id.assert_not_called()

    def test_list_provider_services_user_not_prestador(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        mock_user = MagicMock(id=provider_id, is_active=True, roles={"cliente"})
        mock_user.is_provider.return_value = False
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_provider_service_repository.list_by_provider_id.return_value = [
            MagicMock(
                id=uuid4(),
                provider_id=provider_id,
                service_id=uuid4(),
                price=100.0,
                active=True,
                service_name="Test Service",
                service_description="Test Description",
                created_at=datetime.utcnow(),
            )
        ]

        use_case = ListProviderServicesUseCase(
            mock_provider_service_repository, mock_user_repository
        )

        with pytest.raises(
            ForbiddenError
        ):  
            use_case.execute(input_dto)
