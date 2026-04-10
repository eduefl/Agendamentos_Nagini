"""
Testes de persistência — Fase 1 pagamento.
Cobre:
- ORM do ServiceRequest persiste novos campos financeiros
- PaymentAttempt model persiste todos os campos essenciais
- Repositório mapeia corretamente entidade <-> model para ServiceRequest financeiro
- Repositório mapeia corretamente entidade <-> model para PaymentAttempt
- find_latest_by_service_request_id retorna a tentativa mais recente
- find_by_external_reference encontra pelo external_reference
- count_by_service_request_id conta corretamente
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
import pytest
from domain.payment.payment_attempt_entity import PaymentAttempt
from domain.payment.payment_attempt_status import PaymentAttemptStatus
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


def _add_service(session, make_service, name="Serviço Persist Pagamento"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _make_base_in_progress(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 1",
        status=ServiceRequestStatus.IN_PROGRESS,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        travel_started_at=now + timedelta(minutes=5),
        route_calculated_at=now + timedelta(minutes=5),
        estimated_arrival_at=now + timedelta(minutes=30),
        travel_duration_minutes=25,
        provider_arrived_at=now + timedelta(minutes=28),
        client_confirmed_provider_arrival_at=now + timedelta(minutes=32),
        service_started_at=now + timedelta(minutes=32),
    )


# ─── ServiceRequest financial fields persistence ─────────────────────────────
class TestServiceRequestFinancialFieldsPersistence:
    def test_awaiting_payment_fields_persisted(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Campos de AWAITING_PAYMENT são salvos e recuperados corretamente."""
        cli = _add_user(
            tst_db_session, make_user, name="C1p", email="c1p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P1p",
            email="p1p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Pay1")
        now = datetime.utcnow()
        service_finished = now + timedelta(hours=1)
        payment_requested = now + timedelta(hours=1)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Teste",
            status=ServiceRequestStatus.AWAITING_PAYMENT,
            accepted_provider_id=prov.id,
            departure_address="Rua Origem",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            travel_started_at=now + timedelta(minutes=5),
            route_calculated_at=now + timedelta(minutes=5),
            estimated_arrival_at=now + timedelta(minutes=30),
            travel_duration_minutes=25,
            provider_arrived_at=now + timedelta(minutes=28),
            client_confirmed_provider_arrival_at=now + timedelta(minutes=32),
            service_started_at=now + timedelta(minutes=32),
            service_finished_at=service_finished,
            payment_requested_at=payment_requested,
            payment_amount=Decimal("120.00"),
        )
        repo = ServiceRequestRepository(session=tst_db_session)
        created = repo.create(sr)
        found = repo.find_by_id(created.id)
        assert found is not None
        assert found.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert abs((found.service_finished_at - service_finished).total_seconds()) < 1
        assert abs((found.payment_requested_at - payment_requested).total_seconds()) < 1
        assert found.payment_amount == Decimal("120.00")
        assert found.payment_processing_started_at is None
        assert found.payment_approved_at is None
        assert found.service_concluded_at is None

    def test_completed_fields_persisted(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Campos de COMPLETED são salvos e recuperados corretamente."""
        cli = _add_user(
            tst_db_session, make_user, name="C2p", email="c2p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P2p",
            email="p2p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Pay2")
        now = datetime.utcnow()
        approved_at = now + timedelta(hours=1, minutes=5)
        concluded_at = now + timedelta(hours=1, minutes=5)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Teste",
            status=ServiceRequestStatus.COMPLETED,
            accepted_provider_id=prov.id,
            departure_address="Rua Origem",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            travel_started_at=now + timedelta(minutes=5),
            route_calculated_at=now + timedelta(minutes=5),
            estimated_arrival_at=now + timedelta(minutes=30),
            travel_duration_minutes=25,
            provider_arrived_at=now + timedelta(minutes=28),
            client_confirmed_provider_arrival_at=now + timedelta(minutes=32),
            service_started_at=now + timedelta(minutes=32),
            service_finished_at=now + timedelta(hours=1),
            payment_requested_at=now + timedelta(hours=1),
            payment_processing_started_at=now + timedelta(hours=1, minutes=1),
            payment_approved_at=approved_at,
            service_concluded_at=concluded_at,
            payment_amount=Decimal("120.00"),
            payment_last_status="APPROVED",
            payment_provider="mock-provider",
            payment_reference="ref-abc",
            payment_attempt_count=1,
        )
        repo = ServiceRequestRepository(session=tst_db_session)
        created = repo.create(sr)
        found = repo.find_by_id(created.id)
        assert found is not None
        assert found.status == ServiceRequestStatus.COMPLETED.value
        assert abs((found.payment_approved_at - approved_at).total_seconds()) < 1
        assert abs((found.service_concluded_at - concluded_at).total_seconds()) < 1
        assert found.payment_last_status == "APPROVED"
        assert found.payment_provider == "mock-provider"
        assert found.payment_reference == "ref-abc"
        assert found.payment_attempt_count == 1
        assert found.payment_refused_at is None

    def test_in_progress_null_financial_fields(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """IN_PROGRESS: campos financeiros nulos são persistidos e lidos como None."""
        cli = _add_user(
            tst_db_session, make_user, name="C3p", email="c3p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P3p",
            email="p3p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Pay3")
        sr = _make_base_in_progress(cli.id, svc.id, prov.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        created = repo.create(sr)
        found = repo.find_by_id(created.id)
        assert found.service_finished_at is None
        assert found.payment_requested_at is None
        assert found.payment_processing_started_at is None
        assert found.payment_approved_at is None
        assert found.payment_refused_at is None
        assert found.service_concluded_at is None
        assert found.payment_amount is None
        assert found.payment_last_status is None
        assert found.payment_provider is None
        assert found.payment_reference is None
        assert found.payment_attempt_count is None

    def test_update_propagates_financial_fields(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """update() persiste corretamente campos financeiros."""
        cli = _add_user(
            tst_db_session, make_user, name="C4p", email="c4p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P4p",
            email="p4p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Pay4")
        repo = ServiceRequestRepository(session=tst_db_session)
        sr = _make_base_in_progress(cli.id, svc.id, prov.id)
        created = repo.create(sr)
        now = datetime.utcnow()
        # Simula transição para AWAITING_PAYMENT
        created.status = ServiceRequestStatus.AWAITING_PAYMENT.value
        created.service_finished_at = now + timedelta(hours=1)
        created.payment_requested_at = now + timedelta(hours=1)
        created.payment_amount = Decimal("120.00")
        updated = repo.update(created)
        assert updated.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert updated.service_finished_at is not None
        assert updated.payment_amount == Decimal("120.00")


# ─── PaymentAttempt persistence ──────────────────────────────────────────────
class TestPaymentAttemptPersistence:
    def _make_attempt(self, service_request_id, **overrides):
        kwargs = dict(
            id=uuid4(),
            service_request_id=service_request_id,
            attempt_number=1,
            amount=Decimal("120.00"),
            status=PaymentAttemptStatus.REQUESTED,
            provider="mock-provider",
            external_reference=f"ext-ref-{uuid4().hex[:8]}",
        )
        kwargs.update(overrides)
        return PaymentAttempt(**kwargs)

    def _setup_service_request(self, tst_db_session, make_user, make_service, tag):
        cli = _add_user(
            tst_db_session,
            make_user,
            name=f"Cpa{tag}",
            email=f"cpa{tag}@e.com",
            roles={"cliente"},
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name=f"Ppa{tag}",
            email=f"ppa{tag}@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, f"Serviço Attempt{tag}")
        sr = _make_base_in_progress(cli.id, svc.id, prov.id)
        repo = ServiceRequestRepository(session=tst_db_session)
        return repo.create(sr)

    def test_creates_payment_attempt(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "1")
        repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = self._make_attempt(sr.id)
        created = repo.create(attempt)
        assert created.id is not None
        assert created.service_request_id == sr.id
        assert created.attempt_number == 1
        assert created.amount == Decimal("120.00")
        assert created.status == PaymentAttemptStatus.REQUESTED.value
        assert created.provider == "mock-provider"

    def test_find_latest_by_service_request_id(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "2")
        repo = PaymentAttemptRepository(session=tst_db_session)
        attempt1 = self._make_attempt(
            sr.id, attempt_number=1, external_reference="ref-1"
        )
        attempt2 = self._make_attempt(
            sr.id, attempt_number=2, external_reference="ref-2"
        )
        repo.create(attempt1)
        repo.create(attempt2)
        latest = repo.find_latest_by_service_request_id(sr.id)
        assert latest is not None
        assert latest.attempt_number == 2
        assert latest.external_reference == "ref-2"


    def test_find_by_external_reference(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "3")
        repo = PaymentAttemptRepository(session=tst_db_session)
        ext_ref = f"unique-ref-{uuid4().hex}"
        attempt = self._make_attempt(sr.id, external_reference=ext_ref)
        repo.create(attempt)
        found = repo.find_by_external_reference(ext_ref)
        assert found is not None
        assert found.external_reference == ext_ref

    def test_find_by_external_reference_returns_none_if_not_found(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        _add_user(
            tst_db_session,
            make_user,
            name="Cpax",
            email="cpax@e.com",
            roles={"cliente"},
        )
        repo = PaymentAttemptRepository(session=tst_db_session)
        found = repo.find_by_external_reference("non-existent-ref")
        assert found is None

    def test_count_by_service_request_id(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "4")
        repo = PaymentAttemptRepository(session=tst_db_session)
        assert repo.count_by_service_request_id(sr.id) == 0
        repo.create(
            self._make_attempt(sr.id, attempt_number=1, external_reference="r1")
        )
        assert repo.count_by_service_request_id(sr.id) == 1
        repo.create(
            self._make_attempt(sr.id, attempt_number=2, external_reference="r2")
        )
        assert repo.count_by_service_request_id(sr.id) == 2

    def test_mark_processing(self, tst_db_session, make_user, make_service, seed_roles):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "5")
        repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = self._make_attempt(sr.id)
        created = repo.create(attempt)
        updated = repo.mark_processing(created.id)
        assert updated is not None
        assert updated.status == PaymentAttemptStatus.PROCESSING.value
        assert updated.processing_started_at is not None

    def test_mark_approved(self, tst_db_session, make_user, make_service, seed_roles):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "6")
        repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = self._make_attempt(sr.id)
        created = repo.create(attempt)
        processing = repo.mark_processing(created.id)
        approved = repo.mark_approved(processing.id)
        assert approved is not None
        assert approved.status == PaymentAttemptStatus.APPROVED.value
        assert approved.approved_at is not None
        assert approved.processed_at is not None

    def test_mark_refused_with_reason(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "7")
        repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = self._make_attempt(sr.id)
        created = repo.create(attempt)
        processing = repo.mark_processing(created.id)
        refused = repo.mark_refused(processing.id, refusal_reason="Saldo insuficiente")
        assert refused is not None
        assert refused.status == PaymentAttemptStatus.REFUSED.value
        assert refused.refused_at is not None
        assert refused.processed_at is not None
        assert refused.refusal_reason == "Saldo insuficiente"

    def test_mark_processing_returns_none_if_not_requested(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        sr = self._setup_service_request(tst_db_session, make_user, make_service, "8")
        repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = self._make_attempt(sr.id)
        created = repo.create(attempt)
        repo.mark_processing(created.id)
        # Try mark_processing again (already PROCESSING)
        result = repo.mark_processing(created.id)
        assert result is None
