
"""
Testes unitários dos novos estados operacionais da entidade ServiceRequest.

Cobre:
- Novos valores do enum ServiceRequestStatus
- ServiceRequest aceita CONFIRMED sem campos de deslocamento
- ServiceRequest aceita IN_TRANSIT com campos obrigatórios
- ServiceRequest rejeita IN_TRANSIT sem travel_started_at
- ServiceRequest aceita ARRIVED com campos obrigatórios
- ServiceRequest rejeita ARRIVED sem provider_arrived_at
- ServiceRequest aceita IN_PROGRESS com todos os campos
- ServiceRequest rejeita IN_PROGRESS sem service_started_at
- Rejeição de datas fora de ordem (coerência temporal)
- Campos operacionais rejeitados em status não-operacionais
"""
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)


# ─── helpers ────────────────────────────────────────────────────────────────

def _base_confirmed_kwargs():
    """Kwargs mínimos para um ServiceRequest CONFIRMED válido."""
    now = datetime.utcnow()
    return dict(
        id=uuid4(),
        client_id=uuid4(),
        service_id=uuid4(),
        desired_datetime=now + timedelta(days=1),
        status=ServiceRequestStatus.CONFIRMED,
        address="Rua das Flores, 123",
        accepted_provider_id=uuid4(),
        departure_address="Av. Paulista, 1000",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
    )


def _base_in_transit_kwargs():
    """Kwargs mínimos para um ServiceRequest IN_TRANSIT válido."""
    now = datetime.utcnow()
    return dict(
        id=uuid4(),
        client_id=uuid4(),
        service_id=uuid4(),
        desired_datetime=now + timedelta(days=1),
        status=ServiceRequestStatus.IN_TRANSIT,
        address="Rua das Flores, 123",
        accepted_provider_id=uuid4(),
        departure_address="Av. Paulista, 1000",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        travel_started_at=now + timedelta(minutes=1),
        route_calculated_at=now + timedelta(minutes=1),
        estimated_arrival_at=now + timedelta(minutes=26),
        travel_duration_minutes=25,
    )


def _base_arrived_kwargs():
    """Kwargs mínimos para um ServiceRequest ARRIVED válido."""
    kwargs = _base_in_transit_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = ServiceRequestStatus.ARRIVED
    kwargs["provider_arrived_at"] = now + timedelta(minutes=30)
    return kwargs


def _base_in_progress_kwargs():
    """Kwargs mínimos para um ServiceRequest IN_PROGRESS válido."""
    kwargs = _base_arrived_kwargs()
    now = datetime.utcnow()
    kwargs["status"] = ServiceRequestStatus.IN_PROGRESS
    kwargs["client_confirmed_provider_arrival_at"] = now + timedelta(minutes=32)
    kwargs["service_started_at"] = now + timedelta(minutes=32)
    return kwargs


# ─── Testes do enum ──────────────────────────────────────────────────────────

class TestServiceRequestStatusEnum:
    def test_enum_has_in_transit(self):
        assert ServiceRequestStatus.IN_TRANSIT.value == "IN_TRANSIT"

    def test_enum_has_arrived(self):
        assert ServiceRequestStatus.ARRIVED.value == "ARRIVED"

    def test_enum_has_in_progress(self):
        assert ServiceRequestStatus.IN_PROGRESS.value == "IN_PROGRESS"

    def test_entity_accepts_in_transit_as_string(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["status"] = "IN_TRANSIT"
        sr = ServiceRequest(**kwargs)
        assert sr.status == ServiceRequestStatus.IN_TRANSIT.value

    def test_entity_accepts_arrived_as_string(self):
        kwargs = _base_arrived_kwargs()
        kwargs["status"] = "ARRIVED"
        sr = ServiceRequest(**kwargs)
        assert sr.status == ServiceRequestStatus.ARRIVED.value

    def test_entity_accepts_in_progress_as_string(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["status"] = "IN_PROGRESS"
        sr = ServiceRequest(**kwargs)
        assert sr.status == ServiceRequestStatus.IN_PROGRESS.value


# ─── CONFIRMED: sem campos de deslocamento ───────────────────────────────────

class TestConfirmedState:
    def test_confirmed_valid_without_travel_fields(self):
        sr = ServiceRequest(**_base_confirmed_kwargs())
        assert sr.status == ServiceRequestStatus.CONFIRMED.value
        assert sr.travel_started_at is None
        assert sr.provider_arrived_at is None
        assert sr.service_started_at is None

    def test_confirmed_rejects_travel_started_at(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["travel_started_at"] = datetime.utcnow() + timedelta(minutes=5)
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)


    def test_confirmed_rejects_route_calculated_at(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["route_calculated_at"] = datetime.utcnow() + timedelta(minutes=5)
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)

    def test_confirmed_rejects_estimated_arrival_at(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["estimated_arrival_at"] = datetime.utcnow() + timedelta(minutes=5)
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)

    def test_confirmed_rejects_travel_duration_minutes(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["travel_duration_minutes"] = 30
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)

    def test_confirmed_rejects_travel_distance_km(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["travel_distance_km"] = Decimal("10.0")
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)            
    
    def test_confirmed_rejects_client_confirmed_provider_arrival_at(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["client_confirmed_provider_arrival_at"] = datetime.utcnow() + timedelta(minutes=5)
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)

    def test_confirmed_rejects_provider_arrived_at(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["provider_arrived_at"] = datetime.utcnow() + timedelta(minutes=30)
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)

    def test_confirmed_rejects_service_started_at(self):
        kwargs = _base_confirmed_kwargs()
        kwargs["service_started_at"] = datetime.utcnow() + timedelta(minutes=35)
        with pytest.raises(ValueError, match="Travel and arrival fields can only be set on operational service"):
            ServiceRequest(**kwargs)


# ─── IN_TRANSIT ──────────────────────────────────────────────────────────────

class TestInTransitState:
    def test_in_transit_valid(self):
        sr = ServiceRequest(**_base_in_transit_kwargs())
        assert sr.status == ServiceRequestStatus.IN_TRANSIT.value
        assert sr.travel_started_at is not None
        assert sr.estimated_arrival_at is not None
        assert sr.travel_duration_minutes == 25

    def test_in_transit_accepts_optional_distance(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["travel_distance_km"] = Decimal("8.5")
        sr = ServiceRequest(**kwargs)
        assert sr.travel_distance_km == Decimal("8.5")

    def test_in_transit_rejects_without_travel_started_at(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["travel_started_at"] = None
        with pytest.raises(ValueError, match="must have travel_started_at"):
            ServiceRequest(**kwargs)

    def test_in_transit_rejects_without_route_calculated_at(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["route_calculated_at"] = None
        with pytest.raises(ValueError, match="must have route_calculated_at"):
            ServiceRequest(**kwargs)

    def test_in_transit_rejects_without_estimated_arrival_at(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["estimated_arrival_at"] = None
        with pytest.raises(ValueError, match="must have estimated_arrival_at"):
            ServiceRequest(**kwargs)

    def test_in_transit_rejects_without_travel_duration_minutes(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["travel_duration_minutes"] = None
        with pytest.raises(ValueError, match="must have travel_duration_minutes"):
            ServiceRequest(**kwargs)

    def test_in_transit_rejects_provider_arrived_at(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["provider_arrived_at"] = datetime.utcnow() + timedelta(minutes=30)
        with pytest.raises(ValueError, match="must not have provider_arrived_at"):
            ServiceRequest(**kwargs)

    def test_in_transit_rejects_service_started_at(self):
        kwargs = _base_in_transit_kwargs()
        kwargs["service_started_at"] = datetime.utcnow() + timedelta(minutes=35)
        with pytest.raises(ValueError, match="must not have service_started_at"):
            ServiceRequest(**kwargs)


# ─── ARRIVED ─────────────────────────────────────────────────────────────────

class TestArrivedState:
    def test_arrived_valid(self):
        sr = ServiceRequest(**_base_arrived_kwargs())
        assert sr.status == ServiceRequestStatus.ARRIVED.value
        assert sr.provider_arrived_at is not None

    def test_arrived_rejects_without_provider_arrived_at(self):
        kwargs = _base_arrived_kwargs()
        kwargs["provider_arrived_at"] = None
        with pytest.raises(ValueError, match="must have provider_arrived_at"):
            ServiceRequest(**kwargs)

    def test_arrived_rejects_service_started_at(self):
        kwargs = _base_arrived_kwargs()
        kwargs["service_started_at"] = datetime.utcnow() + timedelta(minutes=35)
        with pytest.raises(ValueError, match="must not have service_started_at"):
            ServiceRequest(**kwargs)

    def test_arrived_rejects_client_confirmed_provider_arrival_at(self):
        kwargs = _base_arrived_kwargs()
        kwargs["client_confirmed_provider_arrival_at"] = datetime.utcnow() + timedelta(minutes=32)
        with pytest.raises(ValueError, match="must not have client_confirmed_provider_arrival_at"):
            ServiceRequest(**kwargs)


# ─── IN_PROGRESS ─────────────────────────────────────────────────────────────

class TestInProgressState:
    def test_in_progress_valid(self):
        sr = ServiceRequest(**_base_in_progress_kwargs())
        assert sr.status == ServiceRequestStatus.IN_PROGRESS.value
        assert sr.service_started_at is not None
        assert sr.client_confirmed_provider_arrival_at is not None

    def test_in_progress_rejects_without_service_started_at(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["service_started_at"] = None
        with pytest.raises(ValueError, match="must have service_started_at"):
            ServiceRequest(**kwargs)

    def test_in_progress_rejects_without_client_confirmed_provider_arrival_at(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["client_confirmed_provider_arrival_at"] = None
        with pytest.raises(ValueError, match="must have client_confirmed_provider_arrival_at"):
            ServiceRequest(**kwargs)

    def test_in_progress_rejects_without_provider_arrived_at(self):
        kwargs = _base_in_progress_kwargs()
        kwargs["provider_arrived_at"] = None
        with pytest.raises(ValueError, match="must have provider_arrived_at"):
            ServiceRequest(**kwargs)


# ─── Coerência temporal ───────────────────────────────────────────────────────

class TestOperationalTemporalOrder:
    def test_rejects_travel_started_at_before_accepted_at(self):
        now = datetime.utcnow()
        kwargs = _base_in_transit_kwargs()
        kwargs["accepted_at"] = now + timedelta(minutes=10)
        kwargs["travel_started_at"] = now  # antes de accepted_at
        kwargs["route_calculated_at"] = now
        kwargs["estimated_arrival_at"] = now + timedelta(minutes=35)
        with pytest.raises(ValueError, match="accepted_at must not be after travel_started_at"):
            ServiceRequest(**kwargs)

    def test_rejects_estimated_arrival_before_travel_started(self):
        now = datetime.utcnow()
        kwargs = _base_in_transit_kwargs()
        kwargs["travel_started_at"] = now + timedelta(minutes=10)
        kwargs["route_calculated_at"] = now + timedelta(minutes=10)
        kwargs["estimated_arrival_at"] = now  # antes de travel_started_at
        with pytest.raises(ValueError, match="travel_started_at must not be after estimated_arrival_at"):
            ServiceRequest(**kwargs)

    def test_rejects_provider_arrived_before_travel_started(self):
        now = datetime.utcnow()
        kwargs = _base_arrived_kwargs()
        kwargs["travel_started_at"] = now + timedelta(minutes=10)
        kwargs["route_calculated_at"] = now + timedelta(minutes=10)
        kwargs["estimated_arrival_at"] = now + timedelta(minutes=35)
        kwargs["provider_arrived_at"] = now  # antes de travel_started_at
        with pytest.raises(ValueError, match="travel_started_at must not be after provider_arrived_at"):
            ServiceRequest(**kwargs)

    def test_rejects_service_started_before_client_confirmed(self):
        now = datetime.utcnow()
        kwargs = _base_in_progress_kwargs()
        kwargs["client_confirmed_provider_arrival_at"] = now + timedelta(minutes=40)
        kwargs["service_started_at"] = now + timedelta(minutes=35)  # antes
        with pytest.raises(ValueError, match="client_confirmed_provider_arrival_at must not be after service_started_at"):
            ServiceRequest(**kwargs)


# ─── Campos operacionais rejeitados em status anteriores ─────────────────────

class TestOperationalFieldsRejectedInNonOperationalStatuses:
    def test_requested_rejects_travel_started_at(self):
        with pytest.raises(ValueError):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.REQUESTED,
                travel_started_at=datetime.utcnow(),
            )

    def test_awaiting_provider_acceptance_rejects_travel_started_at(self):
        with pytest.raises(ValueError):
            ServiceRequest(
                id=uuid4(),
                client_id=uuid4(),
                service_id=uuid4(),
                desired_datetime=datetime.utcnow() + timedelta(days=1),
                status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE,
                travel_started_at=datetime.utcnow(),
            )
