from datetime import datetime, timedelta, timezone
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

# ─── helpers ────────────────────────────────────────────────────────────────

def _base_kwargs():
    return dict(
        id=uuid4(),
        client_id=uuid4(),
        service_id=uuid4(),
        desired_datetime=datetime.utcnow() + timedelta(days=1),
    )


def _confirmed_kwargs():
    now = datetime.utcnow()
    return dict(
        id=uuid4(),
        client_id=uuid4(),
        service_id=uuid4(),
        desired_datetime=now + timedelta(days=1),
        status=ServiceRequestStatus.CONFIRMED,
        address="Rua Destino, 10",
        accepted_provider_id=uuid4(),
        departure_address="Av. Saída, 100",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
    )


def _in_transit_kwargs():
    now = datetime.utcnow()
    kw = _confirmed_kwargs()
    kw.update(
        status=ServiceRequestStatus.IN_TRANSIT,
        travel_started_at=now,
        route_calculated_at=now,
        estimated_arrival_at=now + timedelta(minutes=30),
        travel_duration_minutes=30,
    )
    return kw


def _arrived_kwargs():
    now = datetime.utcnow()
    kw = _in_transit_kwargs()
    kw.update(
        status=ServiceRequestStatus.ARRIVED,
        provider_arrived_at=now + timedelta(minutes=25),
    )
    return kw


def _in_progress_kwargs():
    now = datetime.utcnow()
    kw = _arrived_kwargs()
    kw.update(
        status=ServiceRequestStatus.IN_PROGRESS,
        client_confirmed_provider_arrival_at=now + timedelta(minutes=26),
        service_started_at=now + timedelta(minutes=27),
    )
    return kw


def _awaiting_payment_kwargs():
    now = datetime.utcnow()
    kw = _in_progress_kwargs()
    kw.update(
        status=ServiceRequestStatus.AWAITING_PAYMENT,
        service_finished_at=now + timedelta(minutes=60),
        payment_requested_at=now + timedelta(minutes=61),
        payment_amount=Decimal("120.00"),
    )
    return kw


def _payment_processing_kwargs():
    now = datetime.utcnow()
    kw = _awaiting_payment_kwargs()
    kw.update(
        status=ServiceRequestStatus.PAYMENT_PROCESSING,
        payment_processing_started_at=now + timedelta(minutes=62),
    )
    return kw


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

    def test_with_timezone_aware_desired_datetime_uses_local_now(self):
        tz = timezone.utc
        desired = datetime.now(tz=tz) + timedelta(days=1)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=desired,
        )
        ref = sr._current_reference_datetime()
        assert ref.tzinfo is not None

    def test_with_naive_desired_datetime_uses_utcnow(self):
        desired = datetime.utcnow() + timedelta(days=1)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=desired,
        )
        ref = sr._current_reference_datetime()
        assert ref.tzinfo is None


# ─── validate(): erros nos novos campos opcionais ────────────────────────────

class TestServiceRequestOptionalFieldTypeValidation:
    def test_travel_started_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["travel_started_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="travel_started_at must be a datetime"):
            ServiceRequest(**kw)

    def test_route_calculated_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["route_calculated_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="route_calculated_at must be a datetime"):
            ServiceRequest(**kw)

    def test_estimated_arrival_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["estimated_arrival_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="estimated_arrival_at must be a datetime"):
            ServiceRequest(**kw)

    def test_travel_duration_minutes_must_be_int(self):
        kw = _base_kwargs()
        kw["travel_duration_minutes"] = "30"
        with pytest.raises(ValueError, match="travel_duration_minutes must be an int"):
            ServiceRequest(**kw)

    def test_travel_distance_km_must_be_decimal(self):
        kw = _base_kwargs()
        kw["travel_distance_km"] = "10.5"
        with pytest.raises(ValueError, match="travel_distance_km must be a Decimal"):
            ServiceRequest(**kw)

    def test_provider_arrived_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["provider_arrived_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="provider_arrived_at must be a datetime"):
            ServiceRequest(**kw)

    def test_client_confirmed_provider_arrival_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["client_confirmed_provider_arrival_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="client_confirmed_provider_arrival_at must be a datetime"):
            ServiceRequest(**kw)

    def test_service_started_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["service_started_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="service_started_at must be a datetime"):
            ServiceRequest(**kw)

    def test_logistics_reference_must_be_str(self):
        kw = _base_kwargs()
        kw["logistics_reference"] = 12345
        with pytest.raises(ValueError, match="logistics_reference must be a string"):
            ServiceRequest(**kw)

    def test_service_finished_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["service_finished_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="service_finished_at must be a datetime"):
            ServiceRequest(**kw)

    def test_payment_requested_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["payment_requested_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="payment_requested_at must be a datetime"):
            ServiceRequest(**kw)

    def test_payment_processing_started_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["payment_processing_started_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="payment_processing_started_at must be a datetime"):
            ServiceRequest(**kw)

    def test_payment_approved_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["payment_approved_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="payment_approved_at must be a datetime"):
            ServiceRequest(**kw)

    def test_payment_refused_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["payment_refused_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="payment_refused_at must be a datetime"):
            ServiceRequest(**kw)

    def test_service_concluded_at_must_be_datetime(self):
        kw = _base_kwargs()
        kw["service_concluded_at"] = "2026-01-01"
        with pytest.raises(ValueError, match="service_concluded_at must be a datetime"):
            ServiceRequest(**kw)

    def test_payment_amount_must_be_decimal(self):
        kw = _base_kwargs()
        kw["payment_amount"] = "100.00"
        with pytest.raises(ValueError, match="payment_amount must be a Decimal"):
            ServiceRequest(**kw)

    def test_payment_amount_must_be_positive(self):
        kw = _base_kwargs()
        kw["payment_amount"] = Decimal("-1")
        with pytest.raises(ValueError, match="payment_amount must be greater than zero"):
            ServiceRequest(**kw)

    def test_payment_last_status_must_be_valid_snapshot(self):
        kw = _base_kwargs()
        kw["payment_last_status"] = "INVALID_STATUS"
        with pytest.raises(ValueError, match="payment_last_status must be one of"):
            ServiceRequest(**kw)

    def test_payment_provider_must_be_str(self):
        kw = _base_kwargs()
        kw["payment_provider"] = 999
        with pytest.raises(ValueError, match="payment_provider must be a string"):
            ServiceRequest(**kw)

    def test_payment_reference_must_be_str(self):
        kw = _base_kwargs()
        kw["payment_reference"] = 999
        with pytest.raises(ValueError, match="payment_reference must be a string"):
            ServiceRequest(**kw)

    def test_payment_attempt_count_must_be_int(self):
        kw = _base_kwargs()
        kw["payment_attempt_count"] = "1"
        with pytest.raises(ValueError, match="payment_attempt_count must be an int"):
            ServiceRequest(**kw)

    def test_payment_attempt_count_must_be_non_negative(self):
        kw = _base_kwargs()
        kw["payment_attempt_count"] = -1
        with pytest.raises(ValueError, match="payment_attempt_count must be zero or a positive integer"):
            ServiceRequest(**kw)

    def test_status_invalid_when_mutated(self):
        sr = ServiceRequest(**_base_kwargs())
        sr.status = "COMPLETELY_INVALID"
        with pytest.raises(ValueError, match="Invalid service request status"):
            sr.validate()


# ─── _validate_total_price_consistency ──────────────────────────────────────

class TestTotalPriceConsistency:
    def test_partial_prices_raise_error(self):
        """
        Usa status CANCELLED (que permite campos de precificação) com apenas
        service_price preenchido para acionar a verificação de consistência
        de preços.
        """
        kw = _base_kwargs()
        kw["status"] = ServiceRequestStatus.CANCELLED
        kw["accepted_provider_id"] = uuid4()
        kw["departure_address"] = "Av. Saída, 100"
        kw["service_price"] = Decimal("100.00")
        kw["travel_price"] = None
        kw["total_price"] = None
        kw["accepted_at"] = datetime.utcnow()
        with pytest.raises(ValueError, match="Service price, travel price and total price must be informed together"):
            ServiceRequest(**kw)


# ─── _validate_in_transit_state ─────────────────────────────────────────────

class TestInTransitStateValidation:
    def test_missing_accepted_provider_id(self):
        kw = _in_transit_kwargs()
        kw["accepted_provider_id"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have accepted_provider_id"):
            ServiceRequest(**kw)

    def test_missing_departure_address(self):
        kw = _in_transit_kwargs()
        kw["departure_address"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have departure_address"):
            ServiceRequest(**kw)

    def test_missing_service_price(self):
        kw = _in_transit_kwargs()
        kw["service_price"] = None
        kw["travel_price"] = None
        kw["total_price"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have service_price"):
            ServiceRequest(**kw)

    def test_missing_travel_started_at(self):
        kw = _in_transit_kwargs()
        kw["travel_started_at"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have travel_started_at"):
            ServiceRequest(**kw)

    def test_missing_route_calculated_at(self):
        kw = _in_transit_kwargs()
        kw["route_calculated_at"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have route_calculated_at"):
            ServiceRequest(**kw)

    def test_missing_estimated_arrival_at(self):
        kw = _in_transit_kwargs()
        kw["estimated_arrival_at"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have estimated_arrival_at"):
            ServiceRequest(**kw)

    def test_missing_travel_duration_minutes(self):
        kw = _in_transit_kwargs()
        kw["travel_duration_minutes"] = None
        with pytest.raises(ValueError, match="IN_TRANSIT service request must have travel_duration_minutes"):
            ServiceRequest(**kw)

    def test_must_not_have_provider_arrived_at(self):
        kw = _in_transit_kwargs()
        kw["provider_arrived_at"] = datetime.utcnow()
        with pytest.raises(ValueError, match="IN_TRANSIT service request must not have provider_arrived_at"):
            ServiceRequest(**kw)

    def test_must_not_have_service_started_at(self):
        kw = _in_transit_kwargs()
        kw["service_started_at"] = datetime.utcnow()
        with pytest.raises(ValueError, match="IN_TRANSIT service request must not have service_started_at"):
            ServiceRequest(**kw)


# ─── _validate_arrived_state ─────────────────────────────────────────────────

class TestArrivedStateValidation:
    def test_missing_accepted_provider_id(self):
        kw = _arrived_kwargs()
        kw["accepted_provider_id"] = None
        with pytest.raises(ValueError, match="ARRIVED service request must have accepted_provider_id"):
            ServiceRequest(**kw)

    def test_missing_departure_address(self):
        kw = _arrived_kwargs()
        kw["departure_address"] = None
        with pytest.raises(ValueError, match="ARRIVED service request must have departure_address"):
            ServiceRequest(**kw)

    def test_missing_service_price(self):
        kw = _arrived_kwargs()
        kw["service_price"] = None
        kw["travel_price"] = None
        kw["total_price"] = None
        with pytest.raises(ValueError, match="ARRIVED service request must have service_price"):
            ServiceRequest(**kw)

    def test_missing_provider_arrived_at(self):
        kw = _arrived_kwargs()
        kw["provider_arrived_at"] = None
        with pytest.raises(ValueError, match="ARRIVED service request must have provider_arrived_at"):
            ServiceRequest(**kw)

    def test_must_not_have_service_started_at(self):
        kw = _arrived_kwargs()
        kw["service_started_at"] = datetime.utcnow() + timedelta(minutes=26)
        with pytest.raises(ValueError, match="ARRIVED service request must not have service_started_at"):
            ServiceRequest(**kw)

    def test_must_not_have_client_confirmed_provider_arrival_at(self):
        kw = _arrived_kwargs()
        kw["client_confirmed_provider_arrival_at"] = datetime.utcnow() + timedelta(minutes=26)
        with pytest.raises(ValueError, match="ARRIVED service request must not have client_confirmed_provider_arrival_at"):
            ServiceRequest(**kw)


# ─── _validate_in_progress_state ─────────────────────────────────────────────

class TestInProgressStateValidation:
    def test_missing_accepted_provider_id(self):
        kw = _in_progress_kwargs()
        kw["accepted_provider_id"] = None
        with pytest.raises(ValueError, match="IN_PROGRESS service request must have accepted_provider_id"):
            ServiceRequest(**kw)

    def test_missing_departure_address(self):
        kw = _in_progress_kwargs()
        kw["departure_address"] = None
        with pytest.raises(ValueError, match="IN_PROGRESS service request must have departure_address"):
            ServiceRequest(**kw)

    def test_missing_service_price(self):
        kw = _in_progress_kwargs()
        kw["service_price"] = None
        kw["travel_price"] = None
        kw["total_price"] = None
        with pytest.raises(ValueError, match="IN_PROGRESS service request must have service_price"):
            ServiceRequest(**kw)

    def test_missing_provider_arrived_at(self):
        kw = _in_progress_kwargs()
        kw["provider_arrived_at"] = None
        with pytest.raises(ValueError, match="IN_PROGRESS service request must have provider_arrived_at"):
            ServiceRequest(**kw)

    def test_missing_client_confirmed_provider_arrival_at(self):
        kw = _in_progress_kwargs()
        kw["client_confirmed_provider_arrival_at"] = None
        with pytest.raises(
            ValueError, match="IN_PROGRESS service request must have client_confirmed_provider_arrival_at"
        ):
            ServiceRequest(**kw)

    def test_missing_service_started_at(self):
        kw = _in_progress_kwargs()
        kw["service_started_at"] = None
        with pytest.raises(ValueError, match="IN_PROGRESS service request must have service_started_at"):
            ServiceRequest(**kw)

    def test_must_not_have_financial_fields(self):
        kw = _in_progress_kwargs()
        kw["service_finished_at"] = datetime.utcnow() + timedelta(minutes=90)
        with pytest.raises(ValueError, match="IN_PROGRESS service request must not have financial post-service fields"):
            ServiceRequest(**kw)


# ─── _validate_payment_processing_state ─────────────────────────────────────

class TestPaymentProcessingStateValidation:
    def test_missing_service_started_at(self):
        kw = _payment_processing_kwargs()
        kw["service_started_at"] = None
        with pytest.raises(ValueError, match="PAYMENT_PROCESSING service request must have service_started_at"):
            ServiceRequest(**kw)

    def test_missing_payment_requested_at(self):
        kw = _payment_processing_kwargs()
        kw["payment_requested_at"] = None
        with pytest.raises(ValueError, match="PAYMENT_PROCESSING service request must have payment_requested_at"):
            ServiceRequest(**kw)            