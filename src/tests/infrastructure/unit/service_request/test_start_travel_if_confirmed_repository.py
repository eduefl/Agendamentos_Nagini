from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service_request.sqlalchemy.service_request_model import ServiceRequestModel
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestStartTravelIfConfirmed:
    @staticmethod
    def _create_client(session, make_user):
        repo = userRepository(session=session)
        client = make_user(
            id=uuid4(),
            email=f"{uuid4().hex}@example.com",
            roles={"cliente"},
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
        )
        repo.add_user(client)
        return client

    @staticmethod
    def _create_provider(session, make_user):
        repo = userRepository(session=session)
        provider = make_user(
            id=uuid4(),
            email=f"{uuid4().hex}@example.com",
            roles={"prestador"},
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
        )
        repo.add_user(provider)
        return provider

    @staticmethod
    def _create_service(session):
        service = ServiceModel(
            id=uuid4(),
            name=f"Servico {uuid4().hex}",
            description="Descricao",
        )
        session.add(service)
        session.commit()
        return service

    @staticmethod
    def _create_confirmed_request(session, client_id, provider_id, service_id, expires_delta=None):
        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Destino, 100",
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=provider_id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            expires_at=(now + expires_delta) if expires_delta is not None else None,
        )
        repo = ServiceRequestRepository(session=session)
        return repo.create(sr)

    @staticmethod
    def _make_route_data(now=None):
        if now is None:
            now = datetime.utcnow()
        return {
            "now": now,
            "estimated_arrival_at": now + timedelta(minutes=25),
            "travel_duration_minutes": 25,
            "travel_distance_km": Decimal("8.50"),
            "logistics_reference": "test-ref",
        }

    def test_updates_when_status_confirmed(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_confirmed_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)
        route = self._make_route_data()

        result = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            **route,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.IN_TRANSIT.value
        assert result.travel_started_at is not None
        assert result.route_calculated_at is not None
        assert result.estimated_arrival_at == route["estimated_arrival_at"]
        assert result.travel_duration_minutes == route["travel_duration_minutes"]
        assert result.travel_distance_km == route["travel_distance_km"]
        assert result.logistics_reference == route["logistics_reference"]

    def test_does_not_update_when_status_not_confirmed(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_confirmed_request(session, client.id, provider.id, service.id)

        # Force status to IN_TRANSIT via raw model update (bypassing entity validation)
        session.query(ServiceRequestModel).filter(ServiceRequestModel.id == sr.id).update(
            {
                "status": ServiceRequestStatus.IN_TRANSIT.value,
                "travel_started_at": datetime.utcnow(),
                "route_calculated_at": datetime.utcnow(),
                "estimated_arrival_at": datetime.utcnow() + timedelta(minutes=25),
                "travel_duration_minutes": 25,
            }
        )
        session.commit()

        repo = ServiceRequestRepository(session=session)
        route = self._make_route_data()

        result = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            **route,
        )

        assert result is None

    def test_does_not_update_when_provider_id_does_not_match(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        other_provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_confirmed_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)
        route = self._make_route_data()

        result = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=other_provider.id,
            **route,
        )

        assert result is None

    def test_does_not_update_when_expired(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_confirmed_request(
            session, client.id, provider.id, service.id,
            expires_delta=timedelta(seconds=-1),
        )

        # Ensure expires_at is in the past
        session.query(ServiceRequestModel).filter(ServiceRequestModel.id == sr.id).update(
            {"expires_at": datetime.utcnow() - timedelta(minutes=5)}
        )
        session.commit()

        repo = ServiceRequestRepository(session=session)
        route = self._make_route_data()

        result = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            **route,
        )

        assert result is None

    def test_persists_all_calculated_fields(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_confirmed_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)

        now = datetime.utcnow()
        estimated_arrival = now + timedelta(minutes=30)
        result = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
            estimated_arrival_at=estimated_arrival,
            travel_duration_minutes=30,
            travel_distance_km=Decimal("12.50"),
            logistics_reference="ref-123",
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.IN_TRANSIT.value
        assert result.travel_duration_minutes == 30
        assert result.travel_distance_km == Decimal("12.50")
        assert result.logistics_reference == "ref-123"

    def test_second_call_returns_none_concurrency(self, tst_db_session, make_user, seed_roles):
        """Segunda chamada retorna None porque status já é IN_TRANSIT."""
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_confirmed_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)
        route = self._make_route_data()

        first = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            **route,
        )
        assert first is not None
        assert first.status == ServiceRequestStatus.IN_TRANSIT.value

        second = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            **route,
        )
        assert second is None

    def test_does_not_update_without_expires_at(self, tst_db_session, make_user, seed_roles):
        """Sem expires_at o update deve ocorrer normalmente (expires_at IS NULL)."""
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        # expires_at = None → no expiry constraint
        sr = self._create_confirmed_request(session, client.id, provider.id, service.id, expires_delta=None)
        repo = ServiceRequestRepository(session=session)
        route = self._make_route_data()

        result = repo.start_travel_if_confirmed(
            service_request_id=sr.id,
            provider_id=provider.id,
            **route,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.IN_TRANSIT.value