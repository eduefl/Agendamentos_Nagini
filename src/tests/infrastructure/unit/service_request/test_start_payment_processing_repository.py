"""
Testes de repositório para start_payment_processing_if_awaiting_payment
e start_payment_processing_and_mark_attempt_if_awaiting_payment — Fase 3.
Cobre:
- transição só ocorre quando status está em AWAITING_PAYMENT
- transição só ocorre quando client_id bate
- transição só ocorre quando service_finished_at IS NOT NULL
- transição só ocorre quando payment_requested_at IS NOT NULL (novo)
- transição só ocorre quando payment_amount IS NOT NULL e > 0 (novo)
- segunda chamada retorna None (duplo clique protegido atomicamente)
- payment_processing_started_at é persistido
- payment_last_status vira PROCESSING
- payment_attempt_count permanece inalterado
- PaymentAttempt atual recebe processing_started_at e status=PROCESSING
- método combinado atomicamente atualiza SR e PA em um único commit
- método combinado levanta ServiceRequestPaymentNotRequestedError se PA não está em REQUESTED
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.payment.payment_attempt_entity import PaymentAttempt
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
from infrastructure.service_request.sqlalchemy.service_request_model import ServiceRequestModel
from domain.service_request.service_request_exceptions import ServiceRequestPaymentNotRequestedError
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from infrastructure.payment.sqlalchemy.payment_attempt_model import PaymentAttemptModel


# ─── helpers ─────────────────────────────────────────────────────────────────

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


def _add_service(session, make_service, name="Srv Confirm Payment"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _make_awaiting_payment_sr(client_id, service_id, provider_id, payment_amount=Decimal("150.00")):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 42",
        status=ServiceRequestStatus.AWAITING_PAYMENT,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("120.00"),
        travel_price=Decimal("30.00"),
        total_price=payment_amount,
        accepted_at=now - timedelta(hours=3),
        travel_started_at=now - timedelta(hours=2),
        route_calculated_at=now - timedelta(hours=2),
        estimated_arrival_at=now - timedelta(hours=1, minutes=30),
        travel_duration_minutes=30,
        provider_arrived_at=now - timedelta(hours=1, minutes=25),
        client_confirmed_provider_arrival_at=now - timedelta(hours=1, minutes=20),
        service_started_at=now - timedelta(hours=1, minutes=20),
        service_finished_at=now - timedelta(minutes=10),
        payment_requested_at=now - timedelta(minutes=10),
        payment_amount=payment_amount,
        payment_last_status=PaymentStatusSnapshot.REQUESTED.value,
        payment_attempt_count=1,
    )


def _create_payment_attempt(session, service_request_id, amount=Decimal("150.00")):
    repo = PaymentAttemptRepository(session=session)
    attempt = PaymentAttempt(
        id=uuid4(),
        service_request_id=service_request_id,
        attempt_number=1,
        amount=amount,
        status=PaymentAttemptStatus.REQUESTED.value,
        requested_at=datetime.utcnow() - timedelta(minutes=10),
    )
    result = repo.create(attempt)
    session.commit()
    return result


# ─── testes ──────────────────────────────────────────────────────────────────

class TestStartPaymentProcessingIfAwaitingPayment:

    def test_transitions_awaiting_payment_to_payment_processing(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        result = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=client.id,
            now=now,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.PAYMENT_PROCESSING.value
        assert result.payment_processing_started_at is not None
        assert result.payment_last_status == PaymentStatusSnapshot.PROCESSING.value

    def test_returns_none_if_status_not_awaiting_payment(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        # First create it in AWAITING_PAYMENT, then force it to IN_PROGRESS via model
        from infrastructure.service_request.sqlalchemy.service_request_model import ServiceRequestModel
        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        # Override status via raw model update to bypass entity validation
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update({"status": ServiceRequestStatus.IN_PROGRESS.value, "service_finished_at": None, "payment_requested_at": None, "payment_amount": None, "payment_last_status": None, "payment_attempt_count": None})
        tst_db_session.commit()

        result = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=client.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_returns_none_if_client_id_mismatch(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        other_client = _add_user(tst_db_session, make_user, roles={"cliente"},
                                 name="CLI2", email=f"cli2_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=other_client.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_returns_none_on_second_call(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        r1 = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id, client_id=client.id, now=now
        )
        assert r1 is not None

        r2 = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id, client_id=client.id, now=now
        )
        assert r2 is None

    def test_payment_processing_started_at_is_persisted(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        before = datetime.utcnow()
        repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id, client_id=client.id, now=before
        )
        after = datetime.utcnow()

        persisted = repo.find_by_id(sr.id)
        assert persisted.payment_processing_started_at is not None
        assert before <= persisted.payment_processing_started_at <= after

    def test_payment_last_status_becomes_processing(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id, client_id=client.id, now=datetime.utcnow()
        )

        persisted = repo.find_by_id(sr.id)
        assert persisted.payment_last_status == PaymentStatusSnapshot.PROCESSING.value

    def test_payment_attempt_count_unchanged(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        count_before = repo.find_by_id(sr.id).payment_attempt_count

        repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id, client_id=client.id, now=datetime.utcnow()
        )

        persisted = repo.find_by_id(sr.id)
        assert persisted.payment_attempt_count == count_before

    def test_payment_attempt_mark_processing(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        sr_repo = ServiceRequestRepository(session=tst_db_session)
        sr_repo.create(sr)
        tst_db_session.commit()

        attempt = _create_payment_attempt(tst_db_session, sr.id, sr.payment_amount)

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        before = datetime.utcnow()
        updated_attempt = pa_repo.mark_processing(attempt.id)
        after = datetime.utcnow()

        assert updated_attempt is not None
        assert updated_attempt.status == PaymentAttemptStatus.PROCESSING.value
        assert updated_attempt.processing_started_at is not None
        assert before <= updated_attempt.processing_started_at <= after

    def test_payment_attempt_mark_processing_second_call_returns_none(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        sr_repo = ServiceRequestRepository(session=tst_db_session)
        sr_repo.create(sr)
        tst_db_session.commit()

        attempt = _create_payment_attempt(tst_db_session, sr.id, sr.payment_amount)

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        r1 = pa_repo.mark_processing(attempt.id)
        assert r1 is not None

        r2 = pa_repo.mark_processing(attempt.id)
        assert r2 is None

    def test_returns_none_if_payment_requested_at_is_null(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """payment_requested_at IS NOT NULL é pré-condição obrigatória."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        # Clear payment_requested_at
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update({"payment_requested_at": None})
        tst_db_session.commit()

        result = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=client.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_returns_none_if_payment_amount_is_zero(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """payment_amount <= 0 é rejeitado mesmo com os outros campos preenchidos."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)
        sr_id = uuid4()
        now = datetime.utcnow()

        tst_db_session.add(ServiceRequestModel(
            id=sr_id,
            client_id=client.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            status=ServiceRequestStatus.AWAITING_PAYMENT.value,
            address="Rua Zero, 0",
            accepted_provider_id=provider.id,
            service_price=Decimal("0.00"),
            travel_price=Decimal("0.00"),
            total_price=Decimal("0.00"),
            payment_amount=Decimal("0.00"),
            payment_requested_at=now - timedelta(minutes=10),
            service_finished_at=now - timedelta(minutes=10),
            payment_last_status=PaymentStatusSnapshot.REQUESTED.value,
            payment_attempt_count=1,
        ))
        tst_db_session.commit()

        repo = ServiceRequestRepository(session=tst_db_session)
        result = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=sr_id,
            client_id=client.id,
            now=datetime.utcnow(),
        )

        assert result is None


class TestStartPaymentProcessingAndMarkAttemptAtomic:
    """Testes do método combinado atômico start_payment_processing_and_mark_attempt_if_awaiting_payment."""

    def test_atomically_transitions_sr_and_attempt(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """SR e PA devem ser atualizados no mesmo commit."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        attempt = _create_payment_attempt(tst_db_session, sr.id, sr.payment_amount)
        pa_repo = PaymentAttemptRepository(session=tst_db_session)

        now = datetime.utcnow()
        updated_sr = repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=client.id,
            attempt_id=attempt.id,
            now=now,
        )

        assert updated_sr is not None
        assert updated_sr.status == ServiceRequestStatus.PAYMENT_PROCESSING.value
        assert updated_sr.payment_processing_started_at is not None
        assert updated_sr.payment_last_status == PaymentStatusSnapshot.PROCESSING.value

        updated_attempt = pa_repo.find_latest_by_service_request_id(sr.id)
        assert updated_attempt.status == PaymentAttemptStatus.PROCESSING.value
        assert updated_attempt.processing_started_at is not None

    def test_returns_none_if_sr_condition_not_met(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Retorna None se a pré-condição do ServiceRequest não for satisfeita."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        other_client = _add_user(tst_db_session, make_user, roles={"cliente"},
                                 name="CLI2", email=f"cli2_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        attempt = _create_payment_attempt(tst_db_session, sr.id, sr.payment_amount)

        result = repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=other_client.id,
            attempt_id=attempt.id,
            now=datetime.utcnow(),
        )

        assert result is None
        # SR should still be AWAITING_PAYMENT (rolled back)
        persisted = repo.find_by_id(sr.id)
        assert persisted.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        # PA should still be REQUESTED (rolled back)
        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        pa = pa_repo.find_latest_by_service_request_id(sr.id)
        assert pa.status == PaymentAttemptStatus.REQUESTED.value

    def test_raises_payment_not_requested_if_attempt_not_in_requested(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Levanta ServiceRequestPaymentNotRequestedError quando a PA não está em REQUESTED."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        attempt = _create_payment_attempt(tst_db_session, sr.id, sr.payment_amount)
        # Force attempt to PROCESSING (simulates concurrent call)
        tst_db_session.query(PaymentAttemptModel).filter(
            PaymentAttemptModel.id == attempt.id
        ).update({"status": PaymentAttemptStatus.PROCESSING.value})
        tst_db_session.commit()

        with pytest.raises(ServiceRequestPaymentNotRequestedError):
            repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
                service_request_id=sr.id,
                client_id=client.id,
                attempt_id=attempt.id,
                now=datetime.utcnow(),
            )

        # SR must be rolled back to AWAITING_PAYMENT
        persisted = repo.find_by_id(sr.id)
        assert persisted.status == ServiceRequestStatus.AWAITING_PAYMENT.value

    def test_second_call_returns_none(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Duplo clique: segunda chamada retorna None porque SR já está em PAYMENT_PROCESSING."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"},
                           name="CLI", email=f"cli_{uuid4().hex}@x.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"},
                             name="PROV", email=f"prov_{uuid4().hex}@x.com")
        svc = _add_service(tst_db_session, make_service)

        sr = _make_awaiting_payment_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        attempt = _create_payment_attempt(tst_db_session, sr.id, sr.payment_amount)
        now = datetime.utcnow()

        r1 = repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=client.id,
            attempt_id=attempt.id,
            now=now,
        )
        assert r1 is not None

        r2 = repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id=sr.id,
            client_id=client.id,
            attempt_id=attempt.id,
            now=now,
        )
        assert r2 is None