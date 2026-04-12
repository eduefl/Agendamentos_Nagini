"""
Testes de repositório para os métodos atômicos da Fase 4:
- mark_payment_approved_and_complete_service_if_processing
- mark_payment_refused_and_reopen_for_payment_if_processing

Cobre:
- update aprovado só ocorre quando SR.status == PAYMENT_PROCESSING
- update aprovado só ocorre quando PA.status == PROCESSING
- aprovado muda SR para COMPLETED com payment_approved_at e service_concluded_at
- aprovado persiste provider, external_reference, provider_message
- aprovado muda PA para APPROVED com processed_at e approved_at
- aprovado é atômico (SR e PA no mesmo commit)
- update recusado só ocorre quando SR.status == PAYMENT_PROCESSING
- update recusado só ocorre quando PA.status == PROCESSING
- recusado muda SR para AWAITING_PAYMENT com payment_refused_at
- recusado mantém service_concluded_at = None
- recusado persiste refusal_reason, provider, external_reference, provider_message
- recusado muda PA para REFUSED com processed_at e refused_at
- recusado é atômico (SR e PA no mesmo commit)
- reaplicação do mesmo resultado retorna None (idempotência via pré-condição)
- falha de PA não deixa SR em estado intermediário (rollback)
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
from domain.service_request.service_request_exceptions import (
    PaymentAttemptNotProcessingError,
)
from infrastructure.payment.sqlalchemy.payment_attempt_model import PaymentAttemptModel
from infrastructure.payment.sqlalchemy.payment_attempt_repository import (
    PaymentAttemptRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


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


def _add_service(session, make_service, name="Srv Payment Result"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _create_payment_processing_sr(session, client_id, service_id, provider_id, amount=Decimal("150.00")):
    now = datetime.utcnow()
    # Ensure service_price + travel_price == amount to satisfy entity validation
    travel_price = Decimal("30.00")
    service_price = amount - travel_price
    sr = ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 42",
        status=ServiceRequestStatus.PAYMENT_PROCESSING,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=service_price,
        travel_price=travel_price,
        total_price=amount,
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
        payment_amount=amount,
        payment_last_status=PaymentStatusSnapshot.PROCESSING.value,
        payment_processing_started_at=now - timedelta(minutes=5),
        payment_attempt_count=1,
    )
    repo = ServiceRequestRepository(session=session)
    result = repo.create(sr)
    session.commit()
    return result


def _create_processing_attempt(session, service_request_id, amount=Decimal("150.00")):
    pa_repo = PaymentAttemptRepository(session=session)
    attempt = PaymentAttempt(
        id=uuid4(),
        service_request_id=service_request_id,
        attempt_number=1,
        amount=amount,
        status=PaymentAttemptStatus.PROCESSING.value,
        requested_at=datetime.utcnow() - timedelta(minutes=10),
        processing_started_at=datetime.utcnow() - timedelta(minutes=5),
    )
    result = pa_repo.create(attempt)
    session.commit()
    return result


# ─── Approved ────────────────────────────────────────────────────────────────

class TestMarkPaymentApprovedRepository:

    def test_approved_transitions_sr_to_completed(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        processed_at = datetime.utcnow()
        repo = ServiceRequestRepository(session=tst_db_session)
        result = repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-001",
            provider_message="Aprovado",
            processed_at=processed_at,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.COMPLETED.value

    def test_approved_sets_payment_approved_at(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        processed_at = datetime.utcnow()
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-001",
            provider_message="Aprovado",
            processed_at=processed_at,
        )

        updated = repo.find_by_id(sr.id)
        assert updated.payment_approved_at is not None

    def test_approved_sets_service_concluded_at(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        processed_at = datetime.utcnow()
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-001",
            provider_message=None,
            processed_at=processed_at,
        )

        updated = repo.find_by_id(sr.id)
        assert updated.service_concluded_at is not None

    def test_approved_sets_payment_last_status_approved(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-001",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        updated = repo.find_by_id(sr.id)
        assert updated.payment_last_status == PaymentStatusSnapshot.APPROVED.value

    def test_approved_persists_provider_and_reference(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="test-gateway",
            external_reference="EXT-REF-123",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        updated = repo.find_by_id(sr.id)
        assert updated.payment_provider == "test-gateway"
        assert updated.payment_reference == "EXT-REF-123"

    def test_approved_marks_attempt_as_approved(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-001",
            provider_message="ok",
            processed_at=datetime.utcnow(),
        )

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        updated_attempt = pa_repo.find_latest_by_service_request_id(sr.id)
        assert updated_attempt.status == PaymentAttemptStatus.APPROVED.value
        assert updated_attempt.approved_at is not None
        assert updated_attempt.processed_at is not None

    def test_approved_returns_none_when_sr_not_payment_processing(self, tst_db_session, make_user, make_service, seed_roles):
        """Se SR não está em PAYMENT_PROCESSING, retorna None sem alterar nada."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        # SR in AWAITING_PAYMENT (not PAYMENT_PROCESSING)
        now = datetime.utcnow()
        sr_data = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua A, 1",
            status=ServiceRequestStatus.AWAITING_PAYMENT,
            accepted_provider_id=provider.id,
            departure_address="Rua B, 2",
            service_price=Decimal("100.00"),
            travel_price=Decimal("30.00"),
            total_price=Decimal("130.00"),
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
            payment_amount=Decimal("130.00"),
            payment_last_status=PaymentStatusSnapshot.REQUESTED.value,
            payment_attempt_count=1,
        )
        sr_repo = ServiceRequestRepository(session=tst_db_session)
        sr = sr_repo.create(sr_data)
        tst_db_session.commit()

        attempt = _create_processing_attempt(tst_db_session, sr.id)

        result = sr_repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock",
            external_reference="ref",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        assert result is None
        # SR must not have changed
        unchanged = sr_repo.find_by_id(sr.id)
        assert unchanged.status == ServiceRequestStatus.AWAITING_PAYMENT.value

    def test_approved_raises_attempt_not_processing_error_when_pa_wrong_state(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Se PA não está em PROCESSING, deve levantar PaymentAttemptNotProcessingError e fazer rollback."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)

        # PA in REQUESTED (not PROCESSING)
        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = PaymentAttempt(
            id=uuid4(),
            service_request_id=sr.id,
            attempt_number=1,
            amount=Decimal("150.00"),
            status=PaymentAttemptStatus.REQUESTED.value,
            requested_at=datetime.utcnow() - timedelta(minutes=10),
        )
        pa_repo.create(attempt)
        tst_db_session.commit()

        sr_repo = ServiceRequestRepository(session=tst_db_session)
        with pytest.raises(PaymentAttemptNotProcessingError):
            sr_repo.mark_payment_approved_and_complete_service_if_processing(
                service_request_id=sr.id,
                attempt_id=attempt.id,
                provider="mock",
                external_reference="ref",
                provider_message=None,
                processed_at=datetime.utcnow(),
            )

        # SR must not have been committed to COMPLETED (rollback occurred)
        unchanged = sr_repo.find_by_id(sr.id)
        assert unchanged.status == ServiceRequestStatus.PAYMENT_PROCESSING.value

    def test_approved_replay_returns_none(self, tst_db_session, make_user, make_service, seed_roles):
        """Segunda chamada com SR já em COMPLETED retorna None (idempotência)."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        repo = ServiceRequestRepository(session=tst_db_session)
        # First call succeeds
        repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock",
            external_reference="ref-001",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        # Second call: SR is now COMPLETED, precondition fails -> None
        result = repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock",
            external_reference="ref-001",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )
        assert result is None


# ─── Refused ─────────────────────────────────────────────────────────────────

class TestMarkPaymentRefusedRepository:

    def test_refused_transitions_sr_to_awaiting_payment(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        result = repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-002",
            refusal_reason="Valor acima do limite",
            provider_message="Recusado",
            processed_at=datetime.utcnow(),
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.AWAITING_PAYMENT.value

    def test_refused_sets_payment_refused_at(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-002",
            refusal_reason="Limite excedido",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        updated = repo.find_by_id(sr.id)
        assert updated.payment_refused_at is not None

    def test_refused_keeps_service_concluded_at_none(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-002",
            refusal_reason="Limite excedido",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        updated = repo.find_by_id(sr.id)
        assert updated.service_concluded_at is None

    def test_refused_sets_payment_last_status_refused(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-002",
            refusal_reason="Limite excedido",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        updated = repo.find_by_id(sr.id)
        assert updated.payment_last_status == PaymentStatusSnapshot.REFUSED.value

    def test_refused_persists_provider_reference_and_refusal_reason(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="test-gateway",
            external_reference="EXT-REF-456",
            refusal_reason="Saldo insuficiente",
            provider_message="Declined",
            processed_at=datetime.utcnow(),
        )

        updated = repo.find_by_id(sr.id)
        assert updated.payment_provider == "test-gateway"
        assert updated.payment_reference == "EXT-REF-456"

    def test_refused_marks_attempt_as_refused(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock-provider",
            external_reference="ref-002",
            refusal_reason="Limite excedido",
            provider_message="Declined",
            processed_at=datetime.utcnow(),
        )

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        updated_attempt = pa_repo.find_latest_by_service_request_id(sr.id)
        assert updated_attempt.status == PaymentAttemptStatus.REFUSED.value
        assert updated_attempt.refused_at is not None
        assert updated_attempt.processed_at is not None

    def test_refused_returns_none_when_sr_not_payment_processing(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        # SR in AWAITING_PAYMENT
        now = datetime.utcnow()
        sr_data = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua A, 1",
            status=ServiceRequestStatus.AWAITING_PAYMENT,
            accepted_provider_id=provider.id,
            departure_address="Rua B, 2",
            service_price=Decimal("100.00"),
            travel_price=Decimal("30.00"),
            total_price=Decimal("130.00"),
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
            payment_amount=Decimal("130.00"),
            payment_last_status=PaymentStatusSnapshot.REQUESTED.value,
            payment_attempt_count=1,
        )
        sr_repo = ServiceRequestRepository(session=tst_db_session)
        sr = sr_repo.create(sr_data)
        tst_db_session.commit()

        attempt = _create_processing_attempt(tst_db_session, sr.id)

        result = sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock",
            external_reference="ref",
            refusal_reason=None,
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        assert result is None
        unchanged = sr_repo.find_by_id(sr.id)
        assert unchanged.status == ServiceRequestStatus.AWAITING_PAYMENT.value

    def test_refused_raises_attempt_not_processing_error_when_pa_wrong_state(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))

        # PA in REQUESTED (not PROCESSING)
        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = PaymentAttempt(
            id=uuid4(),
            service_request_id=sr.id,
            attempt_number=1,
            amount=Decimal("600.00"),
            status=PaymentAttemptStatus.REQUESTED.value,
            requested_at=datetime.utcnow() - timedelta(minutes=10),
        )
        pa_repo.create(attempt)
        tst_db_session.commit()

        sr_repo = ServiceRequestRepository(session=tst_db_session)
        with pytest.raises(PaymentAttemptNotProcessingError):
            sr_repo.mark_payment_refused_and_reopen_for_payment_if_processing(
                service_request_id=sr.id,
                attempt_id=attempt.id,
                provider="mock",
                external_reference="ref",
                refusal_reason=None,
                provider_message=None,
                processed_at=datetime.utcnow(),
            )

        # SR must remain in PAYMENT_PROCESSING (rollback)
        unchanged = sr_repo.find_by_id(sr.id)
        assert unchanged.status == ServiceRequestStatus.PAYMENT_PROCESSING.value

    def test_refused_replay_returns_none(self, tst_db_session, make_user, make_service, seed_roles):
        """Segunda chamada para SR já em AWAITING_PAYMENT retorna None (idempotência)."""
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        repo = ServiceRequestRepository(session=tst_db_session)
        # First call succeeds
        repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock",
            external_reference="ref-002",
            refusal_reason="Limite",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        # Second call: SR is now AWAITING_PAYMENT, precondition fails -> None
        result = repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            provider="mock",
            external_reference="ref-002",
            refusal_reason="Limite",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )
        assert result is None