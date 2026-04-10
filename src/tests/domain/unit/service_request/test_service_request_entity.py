from datetime import datetime, timedelta
from decimal import Decimal
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
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE,
        )

        assert service_request.status == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value

    def test_service_request_should_accept_valid_status_string(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(hours=2),
            status="DECLINED",
        )

        assert service_request.status == ServiceRequestStatus.DECLINED.value


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

    def test_service_request_should_raise_error_when_accepted_provider_id_is_invalid(self):
        with pytest.raises(ValueError, match="Accepted provider ID must be a UUID or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                accepted_provider_id="invalid-provider-id",
            )

    def test_service_request_should_raise_error_when_departure_address_is_invalid(self):
        with pytest.raises(ValueError, match="Departure address must be a string or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                departure_address=123,
            )

    def test_service_request_should_raise_error_when_service_price_is_invalid(self):
        with pytest.raises(ValueError, match="Service price must be a Decimal or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                service_price="invalid-price",
            )

    def test_service_request_should_raise_error_when_travel_price_is_invalid(self):
        with pytest.raises(ValueError, match="Travel price must be a Decimal or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                travel_price="invalid-price",
            )

    def test_service_request_should_raise_error_when_total_price_is_invalid(self):
        with pytest.raises(ValueError, match="Total price must be a Decimal or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                total_price="invalid-price",
            )

    def test_service_request_should_raise_error_when_accepted_at_is_invalid(self):
        with pytest.raises(ValueError, match="Accepted at must be a datetime or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                accepted_at="2026-03-31",
            )

    def test_service_request_should_raise_error_when_expires_at_is_invalid(self):
        with pytest.raises(ValueError, match="Expires at must be a datetime or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                expires_at="2026-03-31",
            )
    
    def test_service_request_should_raise_error_when_accepted_provider_id_is_none_in_confirmed_state(self):
        with pytest.raises(ValueError, match="Confirmed service request must have accepted_provider_id."):
            ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=None,
        )

    def test_service_request_should_raise_error_when_departure_address_is_none_in_confirmed_state(self):
        with pytest.raises(ValueError, match="Confirmed service request must have departure_address."):
             ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.CONFIRMED,
                accepted_provider_id=uuid4(),
                departure_address=None,
            )

    def test_service_request_should_raise_error_when_service_price_is_none_in_confirmed_state(self):
        with pytest.raises(ValueError, match="Confirmed service request must have service_price."):
             ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.CONFIRMED,
                accepted_provider_id=uuid4(),
                departure_address="Something",
                service_price=None,
            )

    def test_service_request_should_raise_error_when_travel_price_is_none_in_confirmed_state(self):
        with pytest.raises(ValueError, match="Confirmed service request must have travel_price."):
             ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.CONFIRMED,
                accepted_provider_id=uuid4(),
                departure_address="Something",
                service_price=Decimal('10.00'),
                travel_price=None,
            )

    def test_service_request_should_raise_error_when_total_price_is_none_in_confirmed_state(self):
        with pytest.raises(ValueError, match="Confirmed service request must have total_price."):
             ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.CONFIRMED,
                accepted_provider_id=uuid4(),
                departure_address="Something",
                service_price=Decimal('10.00'),
                travel_price=Decimal('10.00'),
                total_price=None,
            )

    def test_service_request_should_raise_error_when_accepted_at_is_none_in_confirmed_state(self):
        with pytest.raises(ValueError, match="Confirmed service request must have accepted_at."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.CONFIRMED,
                accepted_provider_id=uuid4(),
                departure_address="Something",
                service_price=Decimal('10.00'),
                travel_price=Decimal('10.00'),
                total_price=Decimal('20.00'),
                accepted_at=None,
            )

    def test_service_request_should_raise_error_when_total_price_is_inconsistent(self):
            with pytest.raises(ValueError) as exc_info:
                ServiceRequest(
                    id=uuid4(),
                    client_id=uuid4(),
                    service_id=uuid4(),
                    desired_datetime=datetime.utcnow() + timedelta(days=1),
                    status=ServiceRequestStatus.CONFIRMED,
                    accepted_provider_id=uuid4(),
                    departure_address="Something",
                    service_price=Decimal('10.00'),
                    travel_price=Decimal('5.00'),
                    total_price=Decimal('20.00'),  # Inconsistent total price
                    accepted_at=datetime.utcnow(),
                )
            assert "Total price must be equal to service_price + travel_price." in str(exc_info.value)

    def test_service_request_should_pass_validation_when_all_fields_are_correct_in_confirmed_state(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=uuid4(),
            departure_address="Rua das Flores, 123",
            service_price=Decimal('10.00'),
            travel_price=Decimal('5.00'),
            total_price=Decimal('15.00'),
            accepted_at=datetime.utcnow(),
        )
        assert service_request.validate() is True
        
    def test_service_request_should_raise_error_when_acceptance_fields_are_filled_in_non_confirmed_cancelled_state(self):
        with pytest.raises(ValueError, match="Only confirmed or cancelled service requests can have acceptance and pricing fields filled."):
             ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                accepted_provider_id=uuid4(),
                departure_address="123 Main St",
                service_price=Decimal('100.00'),
                travel_price=Decimal('10.00'),
                total_price=Decimal('110.00'),
                status=ServiceRequestStatus.REQUESTED,
            )

    def test_service_request_should_not_raise_error_when_status_is_confirmed(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            accepted_provider_id=uuid4(),
            departure_address="123 Main St",
            service_price=Decimal('100.00'),
            travel_price=Decimal('10.00'),
            total_price=Decimal('110.00'),
            accepted_at=datetime.utcnow(),
            status=ServiceRequestStatus.CONFIRMED,
        )
        # This should not raise an error
        assert service_request._validate_non_confirmed_cancelled_state() is True

    def test_service_request_should_not_raise_error_when_status_is_cancelled(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            accepted_provider_id=uuid4(),
            departure_address="123 Main St",
            service_price=Decimal('100.00'),
            travel_price=Decimal('10.00'),
            total_price=Decimal('110.00'),
            status=ServiceRequestStatus.CANCELLED,
        )
        # This should not raise an error
        assert service_request._validate_non_confirmed_cancelled_state() is True

    def test_service_request_should_not_raise_error_when_acceptance_fields_are_none_in_non_confirmed_state(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            accepted_provider_id=None,
            departure_address=None,
            service_price=None,
            travel_price=None,
            total_price=None,
            status=ServiceRequestStatus.REQUESTED,
        )
        # This should not raise an error
        assert service_request._validate_non_confirmed_cancelled_state() is True
    def test_service_request_validation_should_pass_with_valid_data(self):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua das Flores, 123",
            created_at=datetime.utcnow(),
            accepted_provider_id=uuid4(),
            departure_address="Rua das Flores, 456",
            service_price=Decimal("100.00"),
            travel_price=Decimal("10.00"),
            total_price=Decimal("110.00"),
            accepted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=2),
            travel_started_at=datetime.utcnow(),
            route_calculated_at=datetime.utcnow(),
            estimated_arrival_at=datetime.utcnow() + timedelta(hours=1),
            travel_duration_minutes=30,
            travel_distance_km=Decimal("5.0"),
            provider_arrived_at=datetime.utcnow(),
            client_confirmed_provider_arrival_at=datetime.utcnow(),
            service_started_at=datetime.utcnow(),
            logistics_reference="LOG123",
            service_finished_at=datetime.utcnow(),
            payment_requested_at=datetime.utcnow(),
            payment_processing_started_at=datetime.utcnow(),
            payment_approved_at=datetime.utcnow(),
            payment_refused_at=None,
            service_concluded_at=datetime.utcnow(),
            payment_amount=Decimal("110.00"),
            payment_last_status="APPROVED",
            payment_provider="Provider A",
            payment_reference="REF123",
            payment_attempt_count=1,
            status=ServiceRequestStatus.COMPLETED,
        )

        assert service_request.validate() is True

    def test_service_request_validation_should_raise_error_for_invalid_id(self):
        with pytest.raises(ValueError, match="ID must be a UUID."):
            ServiceRequest(
                id="invalid-id",
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
            ).validate()

    def test_service_request_validation_should_raise_error_for_invalid_client_id(self):
        with pytest.raises(ValueError, match="Client ID must be a UUID."):
            ServiceRequest(
                id=uuid4(),
                client_id="invalid-client-id",
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
            ).validate()

    def test_service_request_validation_should_raise_error_for_invalid_service_id(self):
        with pytest.raises(ValueError, match="Service ID must be a UUID."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id="invalid-service-id",
                desired_datetime=datetime.utcnow() + timedelta(days=1),
            ).validate()

    def test_service_request_validation_should_raise_error_for_invalid_desired_datetime(self):
        with pytest.raises(ValueError, match="Desired datetime must be a datetime."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime="invalid-datetime",
            ).validate()

    def test_service_request_validation_should_raise_error_for_invalid_address(self):
        with pytest.raises(ValueError, match="Address must be a string or None."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                address=123,
            ).validate()

    def test_service_request_validation_should_raise_error_for_invalid_created_at(self):
        with pytest.raises(ValueError, match="Created at must be a datetime."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                created_at="invalid-datetime",
            ).validate()

    def test_service_request_validation_should_raise_error_for_invalid_payment_amount(self):
        with pytest.raises(ValueError, match="payment_amount must be greater than zero."):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                payment_amount=Decimal("-10.00"),
            ).validate()