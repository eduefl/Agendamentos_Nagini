import pytest
from uuid import uuid4, UUID
from domain.service.service_entity import Service


class TestService:
    def test_service_creation_valid(self):
        service = Service(
            id=uuid4(), name="Test Service", description="A test service."
        )
        assert isinstance(service.id, UUID)
        assert service.name == "Test Service"
        assert service.description == "A test service."

    def test_service_creation_empty_name(self):
        with pytest.raises(ValueError, match="Name cannot be empty."):
            Service(id=uuid4(), name="   ")

    def test_service_creation_invalid_id(self):
        with pytest.raises(ValueError, match="ID must be a valid UUID."):
            Service(id="invalid-uuid", name="Test Service")

    def test_service_creation_invalid_name_type(self):
        with pytest.raises(ValueError, match="Name must be a string."):
            Service(id=uuid4(), name=123)

    def test_service_validation_invalid_description_type(self):
        with pytest.raises(ValueError, match="Description must be a string or None."):
            Service(id=uuid4(), name="Valid Service", description=123)
