from domain.service.service_entity import Service
from domain.service.service_exceptions import ServiceNotFoundError
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
import pytest
from unittest.mock import MagicMock
from uuid import uuid4


class TestServiceMagicMockRepository:
    @pytest.fixture
    def setup(self):
        session = MagicMock()
        repository = ServiceRepository(session)
        return repository, session

    def test_create_service(self, setup):
        repository, session = setup
        service = Service(
            id=uuid4(), name="Test Service", description="A test service."
        )

        repository.create_service(service)

        session.add.assert_called_once()
        session.flush.assert_called_once()

    def test_find_by_id_service_found(self, setup):
        repository, session = setup
        service_id = uuid4()
        service_model = ServiceModel(
            id=service_id, name="test service", description="A test service."
        )
        session.query().filter().first.return_value = service_model

        service = repository.find_by_id(service_id)

        assert service.id == service_id
        assert service.name == "test service"
        assert service.description == "A test service."
        assert isinstance(service, Service)
        assert session.query().filter().first.called

    def test_find_by_id_service_not_found(self, setup):
        repository, session = setup
        service_id = uuid4()
        session.query().filter().first.return_value = None

        with pytest.raises(ServiceNotFoundError):
            repository.find_by_id(service_id)
        assert session.query().filter().first.called
        

    def test_find_by_name_service_found(self, setup):
        repository, session = setup
        not_normalized_name = "Test Service"
        normalized_name = not_normalized_name.strip().lower()
        service_model = ServiceModel(
            id=uuid4(), name=not_normalized_name, description="A test service."
        )
        session.query().filter().first.return_value = service_model

        service = repository.find_by_name(normalized_name)

        assert service.name == normalized_name #_to_entity() normaliza tenho que garantir nao ter duplicidade com sensitivacase
        assert isinstance(service, Service)
        assert session.query().filter().first.called

    def test_find_by_name_service_not_found(self, setup):
        repository, session = setup
        normalized_name = "nonexistent service"
        session.query().filter().first.return_value = None

        service = repository.find_by_name(normalized_name)

        assert service is None
        assert session.query().filter().first.called
