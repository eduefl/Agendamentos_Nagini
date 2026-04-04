from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from infrastructure.security.settings import get_settings
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service.service_exceptions import ServiceNotFoundError
from domain.service.service_repository_interface import ServiceRepositoryInterface
from domain.service_request.service_request_entity import ServiceRequest
from domain.service_request.service_request_exceptions import (
    InvalidServiceRequestDateError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service_request.create_service_request.create_service_request_dto import (
    CreateServiceRequestInputDTO,
    CreateServiceRequestOutputDTO,
)
from usecases.service_request.create_service_request.create_service_request_usecase import (
    CreateServiceRequestUseCase,
)


class TestMockCreateServiceRequestUseCase:
    def test_create_service_request_success(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_service_repository = MagicMock(spec=ServiceRepositoryInterface)
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )

        client_id = uuid4()
        service_id = uuid4()
        desired_datetime = datetime.utcnow() + timedelta(days=1)

        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service = MagicMock(id=service_id)
        mock_service_repository.find_by_id.return_value = mock_service

        mock_service_request_repository.create.side_effect = (
            lambda service_request: service_request
        )
        mock_service_request_repository.update.side_effect = (
            lambda service_request: service_request
        )


        use_case = CreateServiceRequestUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
            service_repository=mock_service_repository,
            provider_service_repository=mock_provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client_id,
            service_id=service_id,
            desired_datetime=desired_datetime,
            address="Rua das Flores, 123",
        )

        settings = get_settings()
        expires_at  = datetime.utcnow() + timedelta(minutes=settings.expire_minutes_request)
        

        output = use_case.execute(input_dto)

        assert isinstance(output, CreateServiceRequestOutputDTO)
        assert output.client_id == client_id
        assert output.service_id == service_id
        assert output.desired_datetime == desired_datetime
        assert output.status == 'AWAITING_PROVIDER_ACCEPTANCE'
        assert output.address == "Rua das Flores, 123"
        assert isinstance(output.created_at, datetime)
        assert output.expires_at > expires_at
        assert output.expires_at < expires_at + timedelta(minutes=1)
        

        mock_user_repository.find_user_by_id.assert_called_once_with(client_id)
        mock_service_repository.find_by_id.assert_called_once_with(service_id)
        mock_service_request_repository.create.assert_called_once()
        mock_provider_service_repository.list_eligible_providers_by_service_id.assert_called_once_with(service_id)


        created_entity = mock_service_request_repository.create.call_args[0][0]
        assert isinstance(created_entity, ServiceRequest)
        assert created_entity.client_id == client_id
        assert created_entity.service_id == service_id
        assert created_entity.desired_datetime == desired_datetime
        assert created_entity.status == 'AWAITING_PROVIDER_ACCEPTANCE'
        assert created_entity.address == "Rua das Flores, 123"

    def test_create_service_request_user_not_found(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_service_repository = MagicMock(spec=ServiceRepositoryInterface)
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )

        client_id = uuid4()
        service_id = uuid4()

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(client_id)

        use_case = CreateServiceRequestUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
            service_repository=mock_service_repository,
            provider_service_repository=mock_provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_service_repository.find_by_id.assert_not_called()
        mock_service_request_repository.create.assert_not_called()

    def test_create_service_request_client_inactive(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_service_repository = MagicMock(spec=ServiceRepositoryInterface)
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )

        client_id = uuid4()
        service_id = uuid4()

        mock_user = MagicMock(id=client_id, is_active=False)
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = CreateServiceRequestUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
            service_repository=mock_service_repository,
            provider_service_repository=mock_provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_service_repository.find_by_id.assert_not_called()
        mock_service_request_repository.create.assert_not_called()

    def test_create_service_request_user_not_client(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_service_repository = MagicMock(spec=ServiceRepositoryInterface)
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )

        client_id = uuid4()
        service_id = uuid4()

        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = False
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = CreateServiceRequestUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
            service_repository=mock_service_repository,
            provider_service_repository=mock_provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_service_repository.find_by_id.assert_not_called()
        mock_service_request_repository.create.assert_not_called()

    def test_create_service_request_service_not_found(self):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_service_repository = MagicMock(spec=ServiceRepositoryInterface)
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )

        client_id = uuid4()
        service_id = uuid4()

        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service_repository.find_by_id.return_value = None

        use_case = CreateServiceRequestUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
            service_repository=mock_service_repository,
            provider_service_repository=mock_provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(ServiceNotFoundError):
            use_case.execute(input_dto)

        mock_service_request_repository.create.assert_not_called()

    def test_create_service_request_should_raise_error_when_desired_datetime_is_in_past(
        self,
    ):
        mock_service_request_repository = MagicMock(
            spec=ServiceRequestRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_service_repository = MagicMock(spec=ServiceRepositoryInterface)
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )

        client_id = uuid4()
        service_id = uuid4()

        mock_user = MagicMock(id=client_id, is_active=True)
        mock_user.is_client.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_service = MagicMock(id=service_id)
        mock_service_repository.find_by_id.return_value = mock_service

        use_case = CreateServiceRequestUseCase(
            service_request_repository=mock_service_request_repository,
            user_repository=mock_user_repository,
            service_repository=mock_service_repository,
            provider_service_repository=mock_provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() - timedelta(minutes=1),
        )

        with pytest.raises(InvalidServiceRequestDateError):
            use_case.execute(input_dto)

        mock_service_request_repository.create.assert_not_called()
