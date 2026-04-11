"""
Testes de integração da Fase 4: ApplyPaymentResultUseCase.
Cobre:
- fluxo de aprovação termina em COMPLETED
- fluxo de recusa volta para AWAITING_PAYMENT
- provider e external_reference ficam persistidos
- service_concluded_at só aparece no aprovado
- service_concluded_at é None no recusado
- notificação aprovado é best effort (falha não desfaz transição)
- notificação recusado é best effort (falha não desfaz transição)
- segunda aplicação de resultado aprovado retorna ServiceRequestAlreadyCompletedError
- segunda aplicação de resultado recusado retorna ServiceRequestPaymentNotProcessingError
- falha de PaymentAttempt (não PROCESSING) levanta PaymentAttemptNotProcessingError e faz rollback
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.payment.payment_attempt_entity import PaymentAttempt
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_dto import PaymentResultDTO
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from domain.service_request.service_request_exceptions import (
    PaymentAttemptNotProcessingError,
    ServiceRequestAlreadyCompletedError,
    ServiceRequestPaymentNotProcessingError,
)
from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)
from infrastructure.payment.sqlalchemy.payment_attempt_repository import (
    PaymentAttemptRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.fakes.fake_email_sender import FakeEmailSender
from usecases.service_request.apply_payment_result.apply_payment_result_usecase import (
    ApplyPaymentResultUseCase,
)


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


def _add_service(session, make_service, name=None):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name or f"Srv {uuid4().hex}")
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


def _build_use_case(session, notification_gateway=None):
    return ApplyPaymentResultUseCase(
        service_request_repository=ServiceRequestRepository(session=session),
        payment_attempt_repository=PaymentAttemptRepository(session=session),
        notification_gateway=notification_gateway,
    )


def _make_approved_result(amount=None):
    return PaymentResultDTO(
        provider="mock-gateway",
        external_reference=f"EXT-{uuid4().hex}",
        status=PaymentAttemptStatus.APPROVED,
        processed_at=datetime.utcnow(),
        provider_message="Pagamento aprovado",
    )


def _make_refused_result():
    return PaymentResultDTO(
        provider="mock-gateway",
        external_reference=f"EXT-{uuid4().hex}",
        status=PaymentAttemptStatus.REFUSED,
        processed_at=datetime.utcnow(),
        refusal_reason="Valor acima do limite",
        provider_message="Pagamento recusado",
    )


# ─── testes de estado ────────────────────────────────────────────────────────

class TestApplyPaymentResultStateIntegration:

    def test_approved_leads_to_completed(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_approved_result(),
            now=datetime.utcnow(),
        )

        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.COMPLETED.value

    def test_approved_sets_payment_approved_at_and_service_concluded_at(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_approved_result(),
            now=datetime.utcnow(),
        )

        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.payment_approved_at is not None
        assert updated.service_concluded_at is not None

    def test_approved_marks_attempt_approved(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_approved_result(),
            now=datetime.utcnow(),
        )

        pa = PaymentAttemptRepository(session=tst_db_session).find_latest_by_service_request_id(sr.id)
        assert pa.status == PaymentAttemptStatus.APPROVED.value
        assert pa.approved_at is not None
        assert pa.processed_at is not None

    def test_refused_leads_to_awaiting_payment(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_refused_result(),
            now=datetime.utcnow(),
        )

        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.AWAITING_PAYMENT.value

    def test_refused_sets_payment_refused_at_but_not_service_concluded_at(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_refused_result(),
            now=datetime.utcnow(),
        )

        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.payment_refused_at is not None
        assert updated.service_concluded_at is None

    def test_refused_marks_attempt_refused(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_refused_result(),
            now=datetime.utcnow(),
        )

        pa = PaymentAttemptRepository(session=tst_db_session).find_latest_by_service_request_id(sr.id)
        assert pa.status == PaymentAttemptStatus.REFUSED.value
        assert pa.refused_at is not None
        assert pa.processed_at is not None

    def test_provider_and_reference_persisted_on_approved(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        result = _make_approved_result()
        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.payment_provider == result.provider
        assert updated.payment_reference == result.external_reference

    def test_provider_and_reference_persisted_on_refused(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        result = _make_refused_result()
        use_case = _build_use_case(tst_db_session)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.payment_provider == result.provider
        assert updated.payment_reference == result.external_reference

    def test_second_approved_call_raises_already_completed(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        result = _make_approved_result()
        use_case = _build_use_case(tst_db_session)

        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        with pytest.raises(ServiceRequestAlreadyCompletedError):
            use_case.execute(
                service_request_id=sr.id,
                attempt_id=attempt.id,
                payment_result=result,
                now=datetime.utcnow(),
            )

    def test_second_refused_call_raises_not_processing(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        result = _make_refused_result()
        use_case = _build_use_case(tst_db_session)

        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        with pytest.raises(ServiceRequestPaymentNotProcessingError):
            use_case.execute(
                service_request_id=sr.id,
                attempt_id=attempt.id,
                payment_result=result,
                now=datetime.utcnow(),
            )

    def test_pa_not_processing_raises_and_does_not_change_sr(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Se PA não está em PROCESSING, erro deve ser levantado e SR permanece inalterado."""
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

        use_case = _build_use_case(tst_db_session)
        with pytest.raises(PaymentAttemptNotProcessingError):
            use_case.execute(
                service_request_id=sr.id,
                attempt_id=attempt.id,
                payment_result=_make_approved_result(),
                now=datetime.utcnow(),
            )

        # SR must remain PAYMENT_PROCESSING
        unchanged = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert unchanged.status == ServiceRequestStatus.PAYMENT_PROCESSING.value


# ─── testes de notificação ───────────────────────────────────────────────────

class TestApplyPaymentResultNotificationIntegration:

    def test_approved_notifies_client_and_provider(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        fake_sender = FakeEmailSender()
        notification_gateway = EmailServiceRequestNotificationGateway(
            email_sender=fake_sender,
            user_repository=userRepository(session=tst_db_session),
        )

        use_case = _build_use_case(tst_db_session, notification_gateway=notification_gateway)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_approved_result(),
            now=datetime.utcnow(),
        )

        assert len(fake_sender.payment_approved_client_notifications_sent) == 1
        assert len(fake_sender.payment_approved_provider_notifications_sent) == 1
        client_notif = fake_sender.payment_approved_client_notifications_sent[0]
        assert client_notif["client_email"] == client.email
        provider_notif = fake_sender.payment_approved_provider_notifications_sent[0]
        assert provider_notif["provider_email"] == provider.email

    def test_refused_notifies_client_and_provider(self, tst_db_session, make_user, make_service, seed_roles):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        fake_sender = FakeEmailSender()
        notification_gateway = EmailServiceRequestNotificationGateway(
            email_sender=fake_sender,
            user_repository=userRepository(session=tst_db_session),
        )

        use_case = _build_use_case(tst_db_session, notification_gateway=notification_gateway)
        result = _make_refused_result()
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=result,
            now=datetime.utcnow(),
        )

        assert len(fake_sender.payment_refused_client_notifications_sent) == 1
        assert len(fake_sender.payment_refused_provider_notifications_sent) == 1
        client_notif = fake_sender.payment_refused_client_notifications_sent[0]
        assert client_notif["client_email"] == client.email
        assert client_notif["refusal_reason"] == result.refusal_reason

    def test_approved_notification_failure_does_not_rollback_transition(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id)
        attempt = _create_processing_attempt(tst_db_session, sr.id)

        failing_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        failing_gateway.notify_payment_approved.side_effect = EmailDeliveryError("mail down")

        use_case = _build_use_case(tst_db_session, notification_gateway=failing_gateway)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_approved_result(),
            now=datetime.utcnow(),
        )

        # Transition must have persisted despite notification failure
        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.COMPLETED.value

    def test_refused_notification_failure_does_not_rollback_transition(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        client = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                           email=f"cli_{uuid4().hex}@example.com")
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_payment_processing_sr(tst_db_session, client.id, svc.id, provider.id, amount=Decimal("600.00"))
        attempt = _create_processing_attempt(tst_db_session, sr.id, amount=Decimal("600.00"))

        failing_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        failing_gateway.notify_payment_refused.side_effect = EmailDeliveryError("mail down")

        use_case = _build_use_case(tst_db_session, notification_gateway=failing_gateway)
        use_case.execute(
            service_request_id=sr.id,
            attempt_id=attempt.id,
            payment_result=_make_refused_result(),
            now=datetime.utcnow(),
        )

        # Transition must have persisted despite notification failure
        updated = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.AWAITING_PAYMENT.value
