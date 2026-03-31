from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from domain.service.service_exceptions import (
    
    ProviderServiceAlreadyActiveError,
    ProviderServiceNotFoundError,
)
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service.activate_provider_service.activate_provider_service_dto import (
    ActivateProviderServiceInputDTO,
    ActivateProviderServiceOutputDTO,
)
from usecases.service.activate_provider_service.activate_provider_service_usecase import (
    ActivateProviderServiceUseCase,
)


class TestMockActivateProviderServiceUseCase:
    def test_activate_provider_service_success(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        provider_service_id = uuid4()
        service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_provider_service = MagicMock(
            id=provider_service_id,
            provider_id=provider_id,
            service_id=service_id,
            active=False,
        )
        mock_provider_service_repository.find_by_id.return_value = mock_provider_service

        updated_provider_service = MagicMock(
            id=provider_service_id,
            provider_id=provider_id,
            service_id=service_id,
            active=True,
        )
        mock_provider_service_repository.update.return_value = updated_provider_service

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, ActivateProviderServiceOutputDTO)
        assert output.provider_service_id == provider_service_id
        assert output.active is True

        mock_user_repository.find_user_by_id.assert_called_once_with(provider_id)
        mock_provider_service_repository.find_by_id.assert_called_once_with(
            provider_service_id
        )
        mock_provider_service.activate.assert_called_once()
        mock_provider_service_repository.update.assert_called_once_with(
            mock_provider_service
        )

    def test_activate_provider_service_user_not_found(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        provider_service_id = uuid4()

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(provider_id)

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_provider_service_repository.find_by_id.assert_not_called()

    def test_activate_provider_service_provider_inactive(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        provider_service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=False)
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_provider_service_repository.find_by_id.assert_not_called()

    def test_activate_provider_service_user_not_provider(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        provider_service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = False
        mock_user_repository.find_user_by_id.return_value = mock_user

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_provider_service_repository.find_by_id.assert_not_called()

    def test_activate_provider_service_not_found(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        provider_service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_provider_service_repository.find_by_id.return_value = None

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        with pytest.raises(ProviderServiceNotFoundError):
            use_case.execute(input_dto)

        mock_provider_service_repository.update.assert_not_called()

    def test_activate_provider_service_from_another_provider(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        other_provider_id = uuid4()
        provider_service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_provider_service = MagicMock(
            id=provider_service_id,
            provider_id=other_provider_id,
            active=False,
        )
        mock_provider_service_repository.find_by_id.return_value = mock_provider_service

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_provider_service_repository.update.assert_not_called()

    def test_activate_provider_service_already_active(self):
        mock_provider_service_repository = MagicMock(
            spec=ProviderServiceRepositoryInterface
        )
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        provider_id = uuid4()
        provider_service_id = uuid4()

        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        mock_user_repository.find_user_by_id.return_value = mock_user

        mock_provider_service = MagicMock(
            id=provider_service_id,
            provider_id=provider_id,
            active=True,
        )
        mock_provider_service.activate.side_effect = ProviderServiceAlreadyActiveError()
        mock_provider_service_repository.find_by_id.return_value = mock_provider_service

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=mock_provider_service_repository,
            user_repository=mock_user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service_id,
        )

        with pytest.raises(ProviderServiceAlreadyActiveError):
            use_case.execute(input_dto)

        mock_provider_service_repository.update.assert_not_called()
