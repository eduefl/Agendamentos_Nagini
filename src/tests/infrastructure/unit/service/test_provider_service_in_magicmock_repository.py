from datetime import datetime
from decimal import Decimal
import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from domain.service.provider_service_entity import ProviderService
from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel


class TestProviderServiceMagicMockRepository:
    @pytest.fixture
    def setup(self):
        session = MagicMock()
        repository = ProviderServiceRepository(session)
        return repository, session

    def test_create_provider_service(self, setup):
        repository, session = setup
        provider_service = ProviderService(
            id=uuid4(),
            provider_id=uuid4(),
            service_id=uuid4(),
            price=Decimal("100.00"),
            active=True,
            created_at=None,
        )

        repository.create_provider_service(provider_service)

        session.add.assert_called_once()
        session.flush.assert_called_once()

    def test_find_by_provider_and_service_found(self, setup):
        repository, session = setup
        provider_id = uuid4()
        service_id = uuid4()
        mock_model = ProviderServiceModel(
            id=uuid4(),
            provider_id=provider_id,
            service_id=service_id,
            price=Decimal("100.00"),
            active=True,
            created_at=datetime.utcnow(),
        )

        session.query().filter().first.return_value = mock_model

        result = repository.find_by_provider_and_service(provider_id, service_id)

        assert result is not None
        assert result.provider_id == provider_id
        assert result.service_id == service_id
        assert result.price == mock_model.price
        assert session.query().filter().first.called

    def test_find_by_provider_and_service_not_found(self, setup):
        repository, session = setup
        provider_id = uuid4()
        service_id = uuid4()

        session.query().filter().first.return_value = None

        result = repository.find_by_provider_and_service(provider_id, service_id)

        assert result is None
        assert session.query().filter().first.called

    def test_list_by_provider_id(self, setup):
        repository, session = setup
        provider_id = uuid4()
        mock_model = ProviderServiceModel(
            id=uuid4(),
            provider_id=provider_id,
            service_id=uuid4(),
            price=Decimal("100.00"),
            active=True,
            created_at=datetime.utcnow(),
        )

        session.query().filter().all.return_value = [mock_model]

        result = repository.list_by_provider_id(provider_id)

        assert len(result) == 1
        assert result[0].provider_id == provider_id
        assert session.query().filter().all.called

    def test_to_entity(self):
        model = ProviderServiceModel(
            id=uuid4(),
            provider_id=uuid4(),
            service_id=uuid4(),
            price=Decimal("100.00"),
            active=True,
            created_at=datetime.utcnow(),
        )

        entity = ProviderServiceRepository._to_entity(model)

        assert entity.id == model.id
        assert entity.provider_id == model.provider_id
        assert entity.service_id == model.service_id
        assert entity.price == model.price
        assert entity.active == model.active
        assert entity.created_at == model.created_at
