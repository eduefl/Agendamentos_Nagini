import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import datetime
from domain.service.provider_service_entity import ProviderService


class TestProviderService:
    def test_provider_service_creation_valid(self):
        provider_service = ProviderService(
            id=uuid4(), provider_id=uuid4(), service_id=uuid4(), price=Decimal("10.00")
        )
        assert isinstance(provider_service.id, UUID)
        assert isinstance(provider_service.provider_id, UUID)
        assert isinstance(provider_service.service_id, UUID)
        assert isinstance(provider_service.price, Decimal)
        assert provider_service.price == Decimal("10.00")
        assert provider_service.active is True
        assert isinstance(provider_service.created_at, datetime)

    def test_provider_service_creation_invalid_id(self):
        with pytest.raises(ValueError, match="ID must be a valid UUID."):
            ProviderService(
                id="invalid-uuid",
                provider_id=uuid4(),
                service_id=uuid4(),
                price=Decimal("10.00"),
            )

    def test_provider_service_creation_invalid_provider_id(self):
        with pytest.raises(ValueError, match="Provider ID must be a valid UUID."):
            ProviderService(
                id=uuid4(),
                provider_id="invalid-uuid",
                service_id=uuid4(),
                price=Decimal("10.00"),
            )

    def test_provider_service_creation_invalid_service_id(self):
        with pytest.raises(ValueError, match="Service ID must be a valid UUID."):
            ProviderService(
                id=uuid4(),
                provider_id=uuid4(),
                service_id="invalid-uuid",
                price=Decimal("10.00"),
            )

    def test_provider_service_creation_invalid_price_type(self):
        with pytest.raises(ValueError, match="Price must be a Decimal."):
            ProviderService(
                id=uuid4(), provider_id=uuid4(), service_id=uuid4(), price="10.00"
            )

    def test_provider_service_creation_negative_price(self):
        with pytest.raises(ValueError, match="Price cannot be negative."):
            ProviderService(
                id=uuid4(),
                provider_id=uuid4(),
                service_id=uuid4(),
                price=Decimal("-10.00"),
            )

    def test_provider_service_creation_invalid_active_type(self):
        with pytest.raises(ValueError, match="Active must be a boolean."):
            ProviderService(
                id=uuid4(),
                provider_id=uuid4(),
                service_id=uuid4(),
                price=Decimal("10.00"),
                active="yes",
            )

    def test_provider_service_creation_invalid_created_at_type(self):
        with pytest.raises(ValueError, match="Created at must be a datetime."):
            ProviderService(
                id=uuid4(),
                provider_id=uuid4(),
                service_id=uuid4(),
                price=Decimal("10.00"),
                created_at="not-a-datetime",
            )
