"""
Testes de integração: notificação best effort ao cliente após finalização do serviço.
Cobre:
- notificação é disparada após transição bem-sucedida
- falha de notificação não desfaz a transição AWAITING_PAYMENT
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
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.fakes.fake_email_sender import FakeEmailSender
from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)
from usecases.service_request.finish_service_and_request_payment.finish_service_and_request_payment_dto import (
    FinishServiceAndRequestPaymentInputDTO,
)
from usecases.service_request.finish_service_and_request_payment.finish_service_and_request_payment_usecase import (
    FinishServiceAndRequestPaymentUseCase,
)


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


def _create_in_progress_sr(session, client_id, service_id, provider_id):
    now = datetime.utcnow()
    sr = ServiceRequest(
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
    repo = ServiceRequestRepository(session=session)
    result = repo.create(sr)
    session.commit()
    return result


def _build_use_case(session, notification_gateway):
    return FinishServiceAndRequestPaymentUseCase(
        service_request_repository=ServiceRequestRepository(session=session),
        notification_gateway=notification_gateway,
    )


class TestFinishServiceNotificationIntegration:
    def test_notification_is_sent_after_success(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov",
                             email=f"prov_{uuid4().hex}@example.com")
        client_user = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli",
                                email=f"cli_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service)
        sr = _create_in_progress_sr(tst_db_session, client_user.id, svc.id, provider.id)

        fake_sender = FakeEmailSender()
        user_repo = userRepository(session=tst_db_session)
        notification_gateway = EmailServiceRequestNotificationGateway(
            email_sender=fake_sender,
            user_repository=user_repo,
        )

        use_case = _build_use_case(tst_db_session, notification_gateway)
        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider.id,
            service_request_id=sr.id,
        )

        output = use_case.execute(input_dto)

        assert output.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert len(fake_sender.payment_requested_notifications_sent) == 1
        notif = fake_sender.payment_requested_notifications_sent[0]
        assert notif["client_email"] == client_user.email
        assert notif["payment_amount"] == Decimal("150.00")

    def test_notification_failure_does_not_rollback_transition(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov2",
                             email=f"prov2_{uuid4().hex}@example.com")
        client_user = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli2",
                                email=f"cli2_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service, name=f"Srv2 {uuid4().hex}")
        sr = _create_in_progress_sr(tst_db_session, client_user.id, svc.id, provider.id)

        failing_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        failing_gateway.notify_payment_requested.side_effect = EmailDeliveryError("mail down")

        use_case = _build_use_case(tst_db_session, failing_gateway)
        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider.id,
            service_request_id=sr.id,
        )

        output = use_case.execute(input_dto)

        # Transition maintained despite notification failure
        assert output.status == ServiceRequestStatus.AWAITING_PAYMENT.value

        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert updated.service_finished_at is not None
        assert updated.payment_requested_at is not None

    def test_client_is_notified_in_best_effort(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(tst_db_session, make_user, roles={"prestador"}, name="Prov3",
                             email=f"prov3_{uuid4().hex}@example.com")
        client_user = _add_user(tst_db_session, make_user, roles={"cliente"}, name="Cli3",
                                email=f"cli3_{uuid4().hex}@example.com")
        svc = _add_service(tst_db_session, make_service, name=f"Srv3 {uuid4().hex}")
        sr = _create_in_progress_sr(tst_db_session, client_user.id, svc.id, provider.id)

        notification_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)

        use_case = _build_use_case(tst_db_session, notification_gateway)
        input_dto = FinishServiceAndRequestPaymentInputDTO(
            authenticated_user_id=provider.id,
            service_request_id=sr.id,
        )

        use_case.execute(input_dto)

        notification_gateway.notify_payment_requested.assert_called_once()
        call_kwargs = notification_gateway.notify_payment_requested.call_args[1]
        assert call_kwargs["client_id"] == client_user.id
        assert call_kwargs["service_request_id"] == sr.id
        assert call_kwargs["payment_amount"] == Decimal("150.00")