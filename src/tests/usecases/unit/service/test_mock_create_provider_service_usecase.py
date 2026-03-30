from decimal import Decimal
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from domain.__seedwork.exceptions import ForbiddenError
from domain.service.service_exceptions import ProviderServiceAlreadyExistsError
from usecases.service.create_provider_service.create_provider_service_dto import (
    CreateProviderServiceInputDTO,
    CreateProviderServiceOutputDTO,
)
from usecases.service.create_provider_service.create_provider_service_usecase import (
    CreateProviderServiceUseCase,
)


class TestMockCreateProviderServiceUseCase(unittest.TestCase):
    def setUp(self):
        self.service_repository = MagicMock()
        self.provider_service_repository = MagicMock()
        self.user_repository = MagicMock()
        self.session = MagicMock()

        self.use_case = CreateProviderServiceUseCase(
            service_repository=self.service_repository,
            provider_service_repository=self.provider_service_repository,
            user_repository=self.user_repository,
            session=self.session,
        )

    def _make_provider(self, roles=None):
        provider = MagicMock()
        provider.id = uuid4()
        provider.roles = roles or ["prestador"]
        return provider

    def test_execute_creates_service_and_provider_service(self):
        input_dto = CreateProviderServiceInputDTO(
            name="Test Service",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
        )

        provider = self._make_provider(["prestador"])
        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_name.return_value = None
        self.provider_service_repository.find_by_provider_and_service.return_value = None

        output = self.use_case.execute(input_dto)

        self.user_repository.find_user_by_id.assert_called_once_with(input_dto.provider_id)
        self.service_repository.create_service.assert_called_once()
        self.provider_service_repository.create_provider_service.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.rollback.assert_not_called()

        self.assertIsInstance(output, CreateProviderServiceOutputDTO)
        self.assertEqual(output.service_name, input_dto.name.strip().lower())

    def test_execute_raises_error_if_provider_service_exists(self):
        input_dto = CreateProviderServiceInputDTO(
            name="Test Service",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
        )

        provider = self._make_provider(["prestador"])
        existing_service = MagicMock()
        existing_service.id = uuid4()
        existing_service.name = input_dto.name.strip().lower()
        existing_service.description = input_dto.description

        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_name.return_value = existing_service
        self.provider_service_repository.find_by_provider_and_service.return_value = MagicMock()

        with self.assertRaises(ProviderServiceAlreadyExistsError):
            self.use_case.execute(input_dto)

        self.service_repository.create_service.assert_not_called()
        self.provider_service_repository.create_provider_service.assert_not_called()
        self.session.commit.assert_not_called()
        self.session.rollback.assert_called_once()

    def test_execute_rolls_back_on_exception(self):
        input_dto = CreateProviderServiceInputDTO(
            name="Test Service",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
        )

        provider = self._make_provider(["prestador"])
        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_name.return_value = None
        self.provider_service_repository.find_by_provider_and_service.return_value = None
        self.provider_service_repository.create_provider_service.side_effect = Exception("Test Exception")

        with self.assertRaises(Exception):
            self.use_case.execute(input_dto)

        self.session.rollback.assert_called_once()
        self.session.commit.assert_not_called()

    def test_execute_creates_provider_service_only_if_service_exists(self):
        input_dto = CreateProviderServiceInputDTO(
            name="Existing Service",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
        )

        provider = self._make_provider(["prestador"])
        existing_service = MagicMock()
        existing_service.id = uuid4()
        existing_service.name = input_dto.name.strip().lower()
        existing_service.description = input_dto.description

        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_name.return_value = existing_service
        self.provider_service_repository.find_by_provider_and_service.return_value = None

        output = self.use_case.execute(input_dto)

        self.service_repository.create_service.assert_not_called()
        self.provider_service_repository.create_provider_service.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.rollback.assert_not_called()

        assert output.service_id == existing_service.id
        assert output.service_name == existing_service.name
        assert isinstance(output, CreateProviderServiceOutputDTO)

    def test_execute_raises_forbidden_if_user_is_not_prestador(self):
        input_dto = CreateProviderServiceInputDTO(
            name="Test Service",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
        )

        provider = self._make_provider(["cliente"])
        self.user_repository.find_user_by_id.return_value = provider

        with self.assertRaises(ForbiddenError):
            self.use_case.execute(input_dto)

        self.service_repository.find_by_name.assert_not_called()
        self.service_repository.create_service.assert_not_called()
        self.provider_service_repository.create_provider_service.assert_not_called()
        self.session.commit.assert_not_called()
        self.session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()