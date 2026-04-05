from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from domain.user.user_exceptions import UserNotFoundError
from domain.service.service_exceptions import ServiceNotFoundError
from tests.fakes.fake_email_sender import FakeEmailSender
from usecases.service_request.notify_service_request_confirmation.notify_service_request_confirmation_service import (
    NotifyServiceRequestConfirmationService,
)


def _make_confirmed_service_request(
    client_id=None,
    service_id=None,
    accepted_provider_id=None,
    service_price=None,
    travel_price=None,
    total_price=None,
    address="Rua Destino, 100",
):
    sp = service_price or Decimal("100.00")
    tp = travel_price or Decimal("25.00")
    tot = total_price or (sp + tp)
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id or uuid4(),
        service_id=service_id or uuid4(),
        desired_datetime=datetime.utcnow() + timedelta(days=1),
        status=ServiceRequestStatus.CONFIRMED.value,
        address=address,
        accepted_provider_id=accepted_provider_id or uuid4(),
        departure_address="Rua Saida, 1",
        service_price=sp,
        travel_price=tp,
        total_price=tot,
        accepted_at=datetime.utcnow(),
    )


def _make_user(name="Test User", email="test@example.com"):
    user = MagicMock()
    user.id = uuid4()
    user.name = name
    user.email = email
    return user


def _make_service(name="Depilacao"):
    service = MagicMock()
    service.id = uuid4()
    service.name = name
    return service


def _make_notification_service(email_sender=None, user_repo=None, service_repo=None):
    return NotifyServiceRequestConfirmationService(
        email_sender=email_sender or FakeEmailSender(),
        user_repository=user_repo or MagicMock(),
        service_repository=service_repo or MagicMock(),
    )


class TestNotifyServiceRequestConfirmationService:
    def test_sends_notification_to_client_with_correct_data(self):
        fake_sender = FakeEmailSender()
        user_repo = MagicMock()
        service_repo = MagicMock()

        client = _make_user(name="Cliente Teste", email="cliente@example.com")
        provider = _make_user(name="Prestador Teste", email="prestador@example.com")
        service = _make_service(name="Massagem")

        service_request = _make_confirmed_service_request(
            client_id=client.id,
            accepted_provider_id=provider.id,
            service_price=Decimal("150.00"),
            travel_price=Decimal("30.00"),
            total_price=Decimal("180.00"),
        )

        user_repo.find_user_by_id.side_effect = lambda uid: (
            client if uid == client.id else provider
        )
        service_repo.find_by_id.return_value = service

        svc = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repo,
            service_repository=service_repo,
        )

        svc.notify(service_request)

        assert len(fake_sender.client_confirmation_notifications_sent) == 1
        notif = fake_sender.client_confirmation_notifications_sent[0]
        assert notif["client_email"] == client.email
        assert notif["client_name"] == client.name
        assert notif["service_name"] == service.name
        assert notif["service_price"] == Decimal("150.00")
        assert notif["travel_price"] == Decimal("30.00")
        assert notif["total_price"] == Decimal("180.00")
        assert notif["status"] == ServiceRequestStatus.CONFIRMED.value

    def test_sends_notification_to_provider_with_correct_data(self):
        fake_sender = FakeEmailSender()
        user_repo = MagicMock()
        service_repo = MagicMock()

        client = _make_user(name="Cliente Teste", email="cliente@example.com")
        provider = _make_user(name="Prestador Teste", email="prestador@example.com")
        service = _make_service(name="Limpeza")

        service_request = _make_confirmed_service_request(
            client_id=client.id,
            accepted_provider_id=provider.id,
            service_price=Decimal("200.00"),
            travel_price=Decimal("50.00"),
            total_price=Decimal("250.00"),
            address="Rua do Cliente, 999",
        )

        user_repo.find_user_by_id.side_effect = lambda uid: (
            client if uid == client.id else provider
        )
        service_repo.find_by_id.return_value = service

        svc = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repo,
            service_repository=service_repo,
        )

        svc.notify(service_request)

        assert len(fake_sender.provider_confirmation_notifications_sent) == 1
        notif = fake_sender.provider_confirmation_notifications_sent[0]
        assert notif["provider_email"] == provider.email
        assert notif["provider_name"] == provider.name
        assert notif["service_name"] == service.name
        assert notif["service_price"] == Decimal("200.00")
        assert notif["service_address"] == "Rua do Cliente, 999"
        assert notif["travel_price"] == Decimal("50.00")
        assert notif["total_price"] == Decimal("250.00")

    def test_raises_if_status_is_not_confirmed(self):
        fake_sender = FakeEmailSender()
        user_repo = MagicMock()
        service_repo = MagicMock()

        sr = MagicMock()
        sr.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value

        svc = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repo,
            service_repository=service_repo,
        )

        with pytest.raises(ValueError):
            svc.notify(sr)

        assert len(fake_sender.client_confirmation_notifications_sent) == 0
        assert len(fake_sender.provider_confirmation_notifications_sent) == 0

    def test_raises_if_client_not_found(self):
        fake_sender = FakeEmailSender()
        user_repo = MagicMock()
        service_repo = MagicMock()

        user_repo.find_user_by_id.side_effect = UserNotFoundError("not found", "id")

        service_request = _make_confirmed_service_request()

        svc = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repo,
            service_repository=service_repo,
        )

        with pytest.raises(UserNotFoundError):
            svc.notify(service_request)

    def test_raises_if_provider_not_found(self):
        fake_sender = FakeEmailSender()
        user_repo = MagicMock()
        service_repo = MagicMock()

        client = _make_user(name="Cliente", email="c@example.com")

        def find_user(uid):
            if uid == client.id:
                return client
            raise UserNotFoundError("not found", "id")

        user_repo.find_user_by_id.side_effect = find_user

        service_request = _make_confirmed_service_request(client_id=client.id)

        svc = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repo,
            service_repository=service_repo,
        )

        with pytest.raises(UserNotFoundError):
            svc.notify(service_request)

    def test_raises_if_service_not_found(self):
        fake_sender = FakeEmailSender()
        user_repo = MagicMock()
        service_repo = MagicMock()

        client = _make_user(name="Cliente", email="c@example.com")
        provider = _make_user(name="Prestador", email="p@example.com")

        user_repo.find_user_by_id.side_effect = lambda uid: (
            client if uid == client.id else provider
        )
        service_repo.find_by_id.side_effect = ServiceNotFoundError("not found", "id")

        service_request = _make_confirmed_service_request(
            client_id=client.id,
            accepted_provider_id=provider.id,
        )

        svc = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repo,
            service_repository=service_repo,
        )

        with pytest.raises(ServiceNotFoundError):
            svc.notify(service_request)