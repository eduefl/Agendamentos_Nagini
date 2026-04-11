"""
Testes de repositório para finish_service_and_open_payment_if_in_progress.
Cobre:
- transição só ocorre quando status está em IN_PROGRESS
- segunda chamada retorna None (atômico — sem dupla finalização)
- payment_attempt_count e payment_last_status ficam consistentes
- service_finished_at e payment_requested_at são persistidos
- PaymentAttempt inicial com attempt_number=1 e status REQUESTED é criado
- payment_amount é congelado corretamente
- external_reference da PaymentAttempt fica nulo
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.payment.sqlalchemy.payment_attempt_repository import (
    PaymentAttemptRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


def _add_user(session, make_user, *, roles, **overrides):
    repo = userRepository(session=session)
    user = make_user(
        id=uuid4(),
        is_active=True,
        activation_code=None,
        activation_code_expires_at=None,
        roles=roles,
        **overrides,
    )
    repo.add_user(user)
    session.commit()
    return user


def _add_service(session, make_service, name="Srv Finish"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _make_in_progress_sr(client_id, service_id, provider_id, total_price=Decimal("150.00")):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Serviço, 42",
        status=ServiceRequestStatus.IN_PROGRESS,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("120.00"),
        travel_price=Decimal("30.00"),
        total_price=total_price,
        accepted_at=now - timedelta(hours=2),
        travel_started_at=now - timedelta(hours=1),
        route_calculated_at=now - timedelta(hours=1),
        estimated_arrival_at=now - timedelta(minutes=30),
        travel_duration_minutes=30,
        provider_arrived_at=now - timedelta(minutes=25),
        client_confirmed_provider_arrival_at=now - timedelta(minutes=20),
        service_started_at=now - timedelta(minutes=20),
    )


class TestFinishServiceAndOpenPaymentRepository:
    def test_transition_occurs_for_in_progress_request(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        payment_amount = Decimal("150.00")
        payment_attempt_id = uuid4()

        result = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
            payment_amount=payment_amount,
            payment_attempt_id=payment_attempt_id,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert result.service_finished_at is not None
        assert result.payment_requested_at is not None
        assert result.payment_amount == payment_amount
        assert result.payment_last_status == PaymentStatusSnapshot.REQUESTED.value
        assert result.payment_attempt_count == 1
        assert result.payment_reference is None
        assert result.payment_provider is None
        assert result.service_concluded_at is None

    def test_second_call_returns_none(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov2")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli2")
        svc = _add_service(tst_db_session, make_service, name=f"Srv2 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        payment_amount = Decimal("150.00")

        first = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
            payment_amount=payment_amount,
            payment_attempt_id=uuid4(),
        )
        assert first is not None

        second = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
            payment_amount=payment_amount,
            payment_attempt_id=uuid4(),
        )
        assert second is None

    def test_does_not_transition_for_non_in_progress_status(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov3")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli3")
        svc = _add_service(tst_db_session, make_service, name=f"Srv3 {uuid4().hex}")

        # Create a CONFIRMED SR (no travel fields — entity validation requires that)
        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Serviço, 42",
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=provider.id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("120.00"),
            travel_price=Decimal("30.00"),
            total_price=Decimal("150.00"),
            accepted_at=now - timedelta(hours=2),
        )
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=datetime.utcnow(),
            payment_amount=Decimal("150.00"),
            payment_attempt_id=uuid4(),
        )

        assert result is None

    def test_does_not_transition_for_wrong_provider(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov4")
        other_provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Other4")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli4")
        svc = _add_service(tst_db_session, make_service, name=f"Srv4 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=other_provider.id,
            now=datetime.utcnow(),
            payment_amount=Decimal("150.00"),
            payment_attempt_id=uuid4(),
        )

        assert result is None

    def test_payment_attempt_is_created_with_correct_fields(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov5")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli5")
        svc = _add_service(tst_db_session, make_service, name=f"Srv5 {uuid4().hex}")

        # total_price must equal service_price + travel_price
        payment_amount = Decimal("150.00")
        sr = _make_in_progress_sr(client.id, svc.id, provider.id, total_price=payment_amount)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        payment_attempt_id = uuid4()

        result = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
            payment_amount=payment_amount,
            payment_attempt_id=payment_attempt_id,
        )

        assert result is not None

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = pa_repo.find_latest_by_service_request_id(sr.id)

        assert attempt is not None
        assert attempt.id == payment_attempt_id
        assert attempt.service_request_id == sr.id
        assert attempt.attempt_number == 1
        assert attempt.amount == payment_amount
        assert attempt.status == PaymentAttemptStatus.REQUESTED.value
        assert attempt.external_reference is None
        assert attempt.provider is None

    def test_timestamps_are_persisted(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov6")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli6")
        svc = _add_service(tst_db_session, make_service, name=f"Srv6 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()

        result = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=now,
            payment_amount=Decimal("150.00"),
            payment_attempt_id=uuid4(),
        )

        assert result is not None
        assert result.service_finished_at is not None
        assert result.payment_requested_at is not None

    def test_payment_attempt_count_is_1_after_first_finalization(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov7")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli7")
        svc = _add_service(tst_db_session, make_service, name=f"Srv7 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.finish_service_and_open_payment_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=datetime.utcnow(),
            payment_amount=Decimal("150.00"),
            payment_attempt_id=uuid4(),
        )

        assert result is not None
        assert result.payment_attempt_count == 1
        assert result.payment_last_status == PaymentStatusSnapshot.REQUESTED.value