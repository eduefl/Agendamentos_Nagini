from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from domain.service_request.service_request_exceptions import (
    InvalidServiceRequestDateError,
)


class TestServiceRequest:
    def test_create_valid_service_request(self):
        desired_datetime = datetime.utcnow() + timedelta(days=1)

        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=desired_datetime,
            address="Rua das Flores, 123",
        )

        assert isinstance(service_request.id, UUID)
        assert isinstance(service_request.client_id, UUID)
        assert isinstance(service_request.service_id, UUID)
        assert service_request.desired_datetime == desired_datetime
        assert service_request.status == ServiceRequestStatus.REQUESTED.value
        assert service_request.address == "Rua das Flores, 123"
        assert isinstance(service_request.created_at, datetime)

    def test_service_request_should_have_requested_status_by_default(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(hours=2),
        )

        assert service_request.status == ServiceRequestStatus.REQUESTED.value

    def test_service_request_should_accept_valid_status_enum(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(hours=2),
            status=ServiceRequestStatus.MATCHING_PROVIDER,
        )

        assert service_request.status == ServiceRequestStatus.MATCHING_PROVIDER.value

    def test_service_request_should_accept_valid_status_string(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(hours=2),
            status="confirmed",
        )

        assert service_request.status == ServiceRequestStatus.CONFIRMED.value


    def test_service_request_should_raise_error_when_created_at_is_invalid(self):
        with pytest.raises(ValueError, match="Created at must be a datetime."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                created_at="2026-03-31",
            )

    def test_service_request_should_raise_error_when_status_is_invalid(self):
        with pytest.raises(ValueError, match="Invalid service request status."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status="INVALID_STATUS",
            )

    def test_service_request_should_raise_error_when_id_is_invalid(self):
        with pytest.raises(ValueError, match="ID must be a UUID."):
            ServiceRequest(
                id="invalid-id",
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
            )

    def test_service_request_should_raise_error_when_client_id_is_invalid(self):
        with pytest.raises(ValueError, match="Client ID must be a UUID."):
            ServiceRequest(
                id=uuid4(),
                client_id="invalid-client-id",
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
            )

    def test_service_request_should_raise_error_when_service_id_is_invalid(self):
        with pytest.raises(ValueError, match="Service ID must be a UUID."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id="invalid-service-id",
                desired_datetime=datetime.utcnow() + timedelta(days=1),
            )

    def test_service_request_should_raise_error_when_address_is_invalid(self):
        with pytest.raises(ValueError, match="Address must be a string or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                address=123,
            )
