
"""
Testes para os caminhos defensivos "model is None após UPDATE bem-sucedido"

"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


# ─── helpers de integração ────────────────────────────────────────────────────

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


def _add_service(session, make_service, name="Srv Legado"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _make_in_progress_sr(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Legado, 1",
        status=ServiceRequestStatus.IN_PROGRESS,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("120.00"),
        travel_price=Decimal("30.00"),
        total_price=Decimal("150.00"),
        accepted_at=now - timedelta(hours=2),
        travel_started_at=now - timedelta(hours=1),
        route_calculated_at=now - timedelta(hours=1),
        estimated_arrival_at=now - timedelta(minutes=30),
        travel_duration_minutes=30,
        provider_arrived_at=now - timedelta(minutes=25),
        client_confirmed_provider_arrival_at=now - timedelta(minutes=20),
        service_started_at=now - timedelta(minutes=20),
    )


def _make_payment_processing_sr(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Legado, 1",
        status=ServiceRequestStatus.PAYMENT_PROCESSING,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("120.00"),
        travel_price=Decimal("30.00"),
        total_price=Decimal("150.00"),
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
        payment_amount=Decimal("150.00"),
        payment_last_status=PaymentStatusSnapshot.PROCESSING.value,
        payment_processing_started_at=now - timedelta(minutes=5),
        payment_attempt_count=1,
    )


# ─── helpers de mock ─────────────────────────────────────────────────────────

def _mock_session_single_execute_rowcount_1_then_none():
    """Sessão cujo único execute() retorna rowcount=1, mas o SELECT subsequente retorna None."""
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.rowcount = 1
    session.execute.return_value = exec_result
    session.query.return_value.filter.return_value.first.return_value = None
    return session


def _mock_session_two_executes_both_rowcount_1_then_none():
    """Sessão com dois execute() (SR + PA) ambos rowcount=1, SELECT final retorna None."""
    session = MagicMock()
    sr_result = MagicMock()
    sr_result.rowcount = 1
    pa_result = MagicMock()
    pa_result.rowcount = 1
    session.execute.side_effect = [sr_result, pa_result]
    session.query.return_value.filter.return_value.first.return_value = None
    return session


# ═════════════════════════════════════════════════════════════════════════════
# 1. _payment_attempt_model_to_entity  (linha 52)
# ═════════════════════════════════════════════════════════════════════════════

class TestPaymentAttemptModelToEntity:
    """Exercita o helper privado _payment_attempt_model_to_entity (linha 52)."""

    def test_maps_all_fields_correctly(self):
        now = datetime.utcnow()
        sid = uuid4()
        aid = uuid4()

        model = MagicMock()
        model.id = aid
        model.service_request_id = sid
        model.attempt_number = 1
        model.amount = Decimal("100.00")
        model.status = PaymentAttemptStatus.REQUESTED.value
        model.requested_at = now
        model.processing_started_at = None
        model.processed_at = None
        model.approved_at = None
        model.refused_at = None
        model.provider = None
        model.external_reference = None
        model.refusal_reason = None
        model.provider_message = None

        repo = ServiceRequestRepository(session=MagicMock())
        entity = repo._payment_attempt_model_to_entity(model)

        assert entity.id == aid
        assert entity.service_request_id == sid
        assert entity.attempt_number == 1
        assert entity.amount == Decimal("100.00")
        assert entity.status == PaymentAttemptStatus.REQUESTED.value
        assert entity.provider is None
        assert entity.external_reference is None


# ═════════════════════════════════════════════════════════════════════════════
# 2. finish_service_if_in_progress  (linhas 557-579)
# ═════════════════════════════════════════════════════════════════════════════

class TestFinishServiceIfInProgress:
    """Testes de integração para o método legado finish_service_if_in_progress."""

    def test_transitions_in_progress_to_awaiting_payment(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvLeg1")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliLeg1")
        svc = _add_service(tst_db_session, make_service, name=f"SrvLeg1 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.finish_service_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=datetime.utcnow(),
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert result.service_finished_at is not None
        assert result.payment_requested_at is not None

    def test_returns_none_when_status_not_in_progress(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvLeg2")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliLeg2")
        svc = _add_service(tst_db_session, make_service, name=f"SrvLeg2 {uuid4().hex}")

        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Legado, 2",
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=provider.id,
            departure_address="Rua Origem, 2",
            service_price=Decimal("120.00"),
            travel_price=Decimal("30.00"),
            total_price=Decimal("150.00"),
            accepted_at=now - timedelta(hours=1),
        )
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.finish_service_if_in_progress(
            service_request_id=sr.id,
            provider_id=provider.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_second_call_returns_none(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvLeg3")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliLeg3")
        svc = _add_service(tst_db_session, make_service, name=f"SrvLeg3 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        first = repo.finish_service_if_in_progress(sr.id, provider.id, now)
        assert first is not None

        second = repo.finish_service_if_in_progress(sr.id, provider.id, now)
        assert second is None


# ═════════════════════════════════════════════════════════════════════════════
# 3. start_payment_processing_if_awaiting_payment – linha 616
# ═════════════════════════════════════════════════════════════════════════════

class TestStartPaymentProcessingModelNoneAfterUpdate:
    """Caminho de corrida: UPDATE rowcount=1 mas SELECT subsequente retorna None (linha 616)."""

    def test_returns_none_when_model_disappears_after_successful_update(self):
        session = _mock_session_single_execute_rowcount_1_then_none()
        repo = ServiceRequestRepository(session=session)

        result = repo.start_payment_processing_if_awaiting_payment(
            service_request_id=uuid4(),
            client_id=uuid4(),
            now=datetime.utcnow(),
        )

        assert result is None
        session.commit.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 4. start_payment_processing_and_mark_attempt_if_awaiting_payment – linha 680
# ═════════════════════════════════════════════════════════════════════════════

class TestStartPaymentProcessingAndMarkAttemptModelNoneAfterUpdate:
    """Caminho de corrida: ambos UPDATEs rowcount=1 mas SELECT final retorna None (linha 680)."""

    def test_returns_none_when_model_disappears_after_successful_update(self):
        session = _mock_session_two_executes_both_rowcount_1_then_none()
        repo = ServiceRequestRepository(session=session)

        result = repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id=uuid4(),
            client_id=uuid4(),
            attempt_id=uuid4(),
            now=datetime.utcnow(),
        )

        assert result is None
        session.commit.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 5. mark_payment_approved_if_processing  (linhas 688-710)
# ═════════════════════════════════════════════════════════════════════════════

class TestMarkPaymentApprovedIfProcessing:
    """Testes de integração para o método legado mark_payment_approved_if_processing."""

    def test_transitions_payment_processing_to_completed(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvApp1")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliApp1")
        svc = _add_service(tst_db_session, make_service, name=f"SrvApp1 {uuid4().hex}")

        sr = _make_payment_processing_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        result = repo.mark_payment_approved_if_processing(
            service_request_id=sr.id,
            now=now,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.COMPLETED.value
        assert result.payment_approved_at is not None
        assert result.service_concluded_at is not None
        assert result.payment_last_status == PaymentStatusSnapshot.APPROVED.value

    def test_returns_none_when_status_not_payment_processing(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvApp2")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliApp2")
        svc = _add_service(tst_db_session, make_service, name=f"SrvApp2 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.mark_payment_approved_if_processing(
            service_request_id=sr.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_second_call_returns_none(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvApp3")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliApp3")
        svc = _add_service(tst_db_session, make_service, name=f"SrvApp3 {uuid4().hex}")

        sr = _make_payment_processing_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        first = repo.mark_payment_approved_if_processing(sr.id, now)
        assert first is not None

        second = repo.mark_payment_approved_if_processing(sr.id, now)
        assert second is None


# ═════════════════════════════════════════════════════════════════════════════
# 6. mark_payment_refused_if_processing  (linhas 717-738)
# ═════════════════════════════════════════════════════════════════════════════

class TestMarkPaymentRefusedIfProcessing:
    """Testes de integração para o método legado mark_payment_refused_if_processing."""

    def test_transitions_payment_processing_to_awaiting_payment(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvRef1")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliRef1")
        svc = _add_service(tst_db_session, make_service, name=f"SrvRef1 {uuid4().hex}")

        sr = _make_payment_processing_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        result = repo.mark_payment_refused_if_processing(
            service_request_id=sr.id,
            now=now,
        )

        assert result is not None
        assert result.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert result.payment_refused_at is not None
        assert result.payment_last_status == PaymentStatusSnapshot.REFUSED.value

    def test_returns_none_when_status_not_payment_processing(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvRef2")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliRef2")
        svc = _add_service(tst_db_session, make_service, name=f"SrvRef2 {uuid4().hex}")

        sr = _make_in_progress_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        result = repo.mark_payment_refused_if_processing(
            service_request_id=sr.id,
            now=datetime.utcnow(),
        )

        assert result is None

    def test_second_call_returns_none(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="ProvRef3")
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="CliRef3")
        svc = _add_service(tst_db_session, make_service, name=f"SrvRef3 {uuid4().hex}")

        sr = _make_payment_processing_sr(client.id, svc.id, provider.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        now = datetime.utcnow()
        first = repo.mark_payment_refused_if_processing(sr.id, now)
        assert first is not None

        second = repo.mark_payment_refused_if_processing(sr.id, now)
        assert second is None


# ═════════════════════════════════════════════════════════════════════════════
# 7. mark_payment_approved_and_complete_service_if_processing – linha 804
# ═════════════════════════════════════════════════════════════════════════════

class TestMarkPaymentApprovedAndCompleteServiceModelNoneAfterUpdate:
    """Caminho de corrida: SR+PA UPDATEs rowcount=1 mas SELECT final retorna None (linha 804)."""

    def test_returns_none_when_model_disappears_after_successful_update(self):
        session = _mock_session_two_executes_both_rowcount_1_then_none()
        repo = ServiceRequestRepository(session=session)

        result = repo.mark_payment_approved_and_complete_service_if_processing(
            service_request_id=uuid4(),
            attempt_id=uuid4(),
            provider="gateway-x",
            external_reference="ref-001",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        assert result is None
        session.commit.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 8. mark_payment_refused_and_reopen_for_payment_if_processing – linha 874
# ═════════════════════════════════════════════════════════════════════════════

class TestMarkPaymentRefusedAndReopenForPaymentModelNoneAfterUpdate:
    """Caminho de corrida: SR+PA UPDATEs rowcount=1 mas SELECT final retorna None (linha 874)."""

    def test_returns_none_when_model_disappears_after_successful_update(self):
        session = _mock_session_two_executes_both_rowcount_1_then_none()
        repo = ServiceRequestRepository(session=session)

        result = repo.mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id=uuid4(),
            attempt_id=uuid4(),
            provider="gateway-x",
            external_reference="ref-002",
            refusal_reason="insufficient_funds",
            provider_message=None,
            processed_at=datetime.utcnow(),
        )

        assert result is None
        session.commit.assert_called_once()
