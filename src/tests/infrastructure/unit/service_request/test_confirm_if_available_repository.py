from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service_request.sqlalchemy.service_request_model import ServiceRequestModel
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestConfirmIfAvailable:
    @staticmethod
    def _create_client(session, make_user):
        repo = userRepository(session=session)
        client = make_user(
            id=uuid4(),
            email=f"{uuid4()}@example.com",
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
            email=f"{uuid4()}@example.com",
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
            name=f"Servico {uuid4()}",
            description="Descricao",
        )
        session.add(service)
        session.commit()
        return service

    @staticmethod
    def _create_service_request(session, client_id, service_id, status, expires_delta=timedelta(hours=1)):
        repo = ServiceRequestRepository(session=session)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua Destino, 100",
            status=status,
            expires_at=datetime.utcnow() + expires_delta,
        )
        return repo.create(sr)

    def test_confirms_when_available(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_service_request(
            session, client.id, service.id, ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        )

        repo = ServiceRequestRepository(session=session)

        service_price = Decimal("100.00")
        travel_price = Decimal("20.00")
        total_price = Decimal("120.00")
        accepted_at = datetime.utcnow()

        result = repo.confirm_if_available(
            service_request_id=sr.id,
            accepted_provider_id=provider.id,
            departure_address="Rua Saída, 1",
            service_price=service_price,
            travel_price=travel_price,
            total_price=total_price,
            accepted_at=accepted_at,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.CONFIRMED.value
        assert result.accepted_provider_id == provider.id
        assert result.departure_address == "Rua Saída, 1"
        assert result.service_price == service_price
        assert result.travel_price == travel_price
        assert result.total_price == total_price
        assert result.accepted_at is not None

    def test_does_not_confirm_when_already_confirmed(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_service_request(
            session, client.id, service.id, ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        )
        sr.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        sr.expires_at = datetime.utcnow() + timedelta(hours=1)
        repo = ServiceRequestRepository(session=session)
        repo.update(sr)

        # First provider confirms
        repo.confirm_if_available(
            service_request_id=sr.id,
            accepted_provider_id=provider.id,
            departure_address="Rua A, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("10.00"),
            total_price=Decimal("110.00"),
            accepted_at=datetime.utcnow(),
        )

        # Second provider tries to confirm the same request
        provider2 = self._create_provider(session, make_user)
        result = repo.confirm_if_available(
            service_request_id=sr.id,
            accepted_provider_id=provider2.id,
            departure_address="Rua B, 2",
            service_price=Decimal("90.00"),
            travel_price=Decimal("15.00"),
            total_price=Decimal("105.00"),
            accepted_at=datetime.utcnow(),
        )

        assert result is None

    def test_does_not_confirm_when_expired(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_service_request(
            session, client.id, service.id, ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_delta=timedelta(seconds=-1),
        )
        sr.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        sr.expires_at = datetime.utcnow() - timedelta(minutes=1)
        repo = ServiceRequestRepository(session=session)
        repo.update(sr)

        result = repo.confirm_if_available(
            service_request_id=sr.id,
            accepted_provider_id=provider.id,
            departure_address="Rua A, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("10.00"),
            total_price=Decimal("110.00"),
            accepted_at=datetime.utcnow(),
        )

        assert result is None

    def test_does_not_confirm_when_wrong_status(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_client(session, make_user)
        provider = self._create_provider(session, make_user)
        service = self._create_service(session)

        sr = self._create_service_request(
            session, client.id, service.id, ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        )
        # Use raw model update to force a non-accepting status, bypassing entity validation
        session.query(ServiceRequestModel).filter(ServiceRequestModel.id == sr.id).update(
            {"status": ServiceRequestStatus.CANCELLED.value}
        )
        session.commit()

        repo = ServiceRequestRepository(session=session)
        result = repo.confirm_if_available(
            service_request_id=sr.id,
            accepted_provider_id=provider.id,
            departure_address="Rua A, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("10.00"),
            total_price=Decimal("110.00"),
            accepted_at=datetime.utcnow(),
        )

        assert result is None