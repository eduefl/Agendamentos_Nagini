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


class TestMarkArrivedIfInTransit:
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
    def _create_in_transit_request(session, client_id, provider_id, service_id):
        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Destino, 100",
            status=ServiceRequestStatus.IN_TRANSIT,
            accepted_provider_id=provider_id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now - timedelta(hours=1),
            travel_started_at=now - timedelta(minutes=15),
            route_calculated_at=now - timedelta(minutes=15),
            estimated_arrival_at=now + timedelta(minutes=10),
            travel_duration_minutes=25,
        )
        repo = ServiceRequestRepository(session=session)
        return repo.create(sr)

    def test_updates_when_status_in_transit(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_in_transit_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)
        now = datetime.utcnow()

        result = repo.mark_arrived_if_in_transit(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.ARRIVED.value
        assert result.provider_arrived_at is not None

    def test_does_not_update_when_status_not_in_transit(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_in_transit_request(session, client.id, provider.id, service.id)

        # Force status to ARRIVED via raw update
        session.query(ServiceRequestModel).filter(ServiceRequestModel.id == sr.id).update(
            {
                "status": ServiceRequestStatus.ARRIVED.value,
                "provider_arrived_at": datetime.utcnow(),
            }
        )
        session.commit()

        repo = ServiceRequestRepository(session=session)

        result = repo.mark_arrived_if_in_transit(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_does_not_update_when_provider_id_does_not_match(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        other_provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_in_transit_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)

        result = repo.mark_arrived_if_in_transit(
            service_request_id=sr.id,
            provider_id=other_provider.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_persists_provider_arrived_at(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_in_transit_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)

        # Use a now that is after travel_started_at but in the future
        fixed_now = datetime.utcnow() + timedelta(minutes=5)
        result = repo.mark_arrived_if_in_transit(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=fixed_now,
        )

        assert result is not None
        assert result.provider_arrived_at == fixed_now
        assert result.status == ServiceRequestStatus.ARRIVED.value

    def test_second_call_returns_none_concurrency(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_in_transit_request(session, client.id, provider.id, service.id)
        repo = ServiceRequestRepository(session=session)
        now = datetime.utcnow()

        first = repo.mark_arrived_if_in_transit(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
        )
        assert first is not None
        assert first.status == ServiceRequestStatus.ARRIVED.value

        second = repo.mark_arrived_if_in_transit(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
        )
        assert second is None