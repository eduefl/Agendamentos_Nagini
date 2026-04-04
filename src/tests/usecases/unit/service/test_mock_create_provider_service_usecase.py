from decimal import Decimal
import unittest
from unittest.mock import MagicMock
from uuid import uuid4
from pydantic import ValidationError


from domain.__seedwork.exceptions import ForbiddenError
from domain.service.service_exceptions import (
    ProviderServiceAlreadyExistsError,
    ServiceNotFoundError,
)
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
        self.provider_service_repository.find_by_provider_and_service.return_value = (
            None
        )

        output = self.use_case.execute(input_dto)

        self.user_repository.find_user_by_id.assert_called_once_with(
            input_dto.provider_id
        )
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
        self.provider_service_repository.find_by_provider_and_service.return_value = (
            MagicMock()
        )

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
        self.provider_service_repository.find_by_provider_and_service.return_value = (
            None
        )
        self.provider_service_repository.create_provider_service.side_effect = (
            Exception("Test Exception")
        )

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
        self.provider_service_repository.find_by_provider_and_service.return_value = (
            None
        )

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

    def test_execute_does_not_create_duplicate_service(self):
        input_dto = CreateProviderServiceInputDTO(
            name=" SERVICE 1 ",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
        )

        provider = self._make_provider(["prestador"])
        existing_service = MagicMock()
        existing_service.id = uuid4()
        existing_service.name = "service 1"
        existing_service.description = input_dto.description

        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_name.return_value = existing_service
        self.provider_service_repository.find_by_provider_and_service.return_value = (
            None
        )

        output = self.use_case.execute(input_dto)

        self.service_repository.create_service.assert_not_called()
        self.provider_service_repository.create_provider_service.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.rollback.assert_not_called()

        assert output.service_id == existing_service.id
        assert output.service_name == existing_service.name
        assert isinstance(output, CreateProviderServiceOutputDTO)

    # validate when name is empty and service_id is empty or when both are filled, should raise ValueError
    def test_execute_raises_value_error_if_name_and_service_id_both_empty_or_both_filled(
        self,
    ):
        with self.assertRaises(ValidationError):
            input_dto = CreateProviderServiceInputDTO(
                name="   ",
                description="Test Description",
                provider_id=uuid4(),
                price=Decimal("100.00"),
            )

        with self.assertRaises(ValidationError):
            input_dto = CreateProviderServiceInputDTO(
                description="Test Description",
                provider_id=uuid4(),
                price=Decimal("100.00"),
            )

        with self.assertRaises(ValidationError):
            input_dto = CreateProviderServiceInputDTO(
                name="Filed",
                description="Test Description",
                provider_id=uuid4(),
                price=Decimal("100.00"),
                service_id=uuid4(),
            )

    # validate when service_id is filled but service does not exist, should raise ServiceNotFoundError
    def test_execute_raises_service_not_found_error_if_service_id_filled_but_service_not_exist(
        self,
    ):
        input_dto = CreateProviderServiceInputDTO(
            name="   ",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
            service_id=uuid4(),
        )

        provider = self._make_provider(["prestador"])
        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_id.side_effect = ServiceNotFoundError(
            value=str(input_dto.service_id),
            attribute="id",
        )

        with self.assertRaises(ServiceNotFoundError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Service ", str(context.exception))
        self.assertIn("not found", str(context.exception))

    # validate when service_id is filled and service exist, should create provider service with that service_id
    def test_execute_creates_provider_service_with_existing_service_id(self):
        service_id = uuid4()
        input_dto = CreateProviderServiceInputDTO(
            name="   ",
            description="Test Description",
            provider_id=uuid4(),
            price=Decimal("100.00"),
            service_id=service_id,
        )

        provider = self._make_provider(["prestador"])
        existing_service = MagicMock()
        existing_service.id = service_id
        existing_service.name = "existing service"
        existing_service.description = input_dto.description

        self.user_repository.find_user_by_id.return_value = provider
        self.service_repository.find_by_id.return_value = existing_service
        self.provider_service_repository.find_by_provider_and_service.return_value = (
            None
        )

        output = self.use_case.execute(input_dto)

        self.service_repository.create_service.assert_not_called()
        self.provider_service_repository.create_provider_service.assert_called_once()
        self.user_repository.find_user_by_id.assert_called_once_with(
            input_dto.provider_id
        )
        self.service_repository.find_by_id.assert_called_once_with(input_dto.service_id)
        self.service_repository.find_by_name.assert_not_called()
        self.session.commit.assert_called_once()
        self.session.rollback.assert_not_called()

        assert output.service_id == existing_service.id
        assert output.service_name == existing_service.name
        assert isinstance(output, CreateProviderServiceOutputDTO)


if __name__ == "__main__":
    unittest.main()
