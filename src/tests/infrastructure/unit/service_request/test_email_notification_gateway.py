"""
Unit tests for EmailServiceRequestNotificationGateway error paths.
Covers the cases where client or provider is not found in the repository.
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.notification.notification_exceptions import EmailDeliveryError
from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)


def _make_gateway(client=None, provider=None):
    email_sender = MagicMock()
    user_repo = MagicMock()
    user_repo.find_user_by_id.side_effect = lambda user_id: None
    gateway = EmailServiceRequestNotificationGateway(
        email_sender=email_sender,
        user_repository=user_repo,
    )
    return gateway, email_sender, user_repo


class TestEmailNotificationGatewayClientNotFound:
    def test_notify_client_travel_started_raises_when_client_not_found(self):
        gateway, _, _ = _make_gateway()
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_client_travel_started(
                client_id=uuid4(),
                service_request_id=uuid4(),
                estimated_arrival_at=datetime.utcnow(),
                travel_duration_minutes=30,
            )

    def test_notify_client_provider_arrived_raises_when_client_not_found(self):
        gateway, _, _ = _make_gateway()
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_client_provider_arrived(
                client_id=uuid4(),
                service_request_id=uuid4(),
                provider_arrived_at=datetime.utcnow(),
            )

    def test_notify_payment_requested_raises_when_client_not_found(self):
        gateway, _, _ = _make_gateway()
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_payment_requested(
                client_id=uuid4(),
                service_request_id=uuid4(),
                payment_amount=Decimal("100.00"),
                payment_requested_at=datetime.utcnow(),
            )

    def test_notify_payment_approved_raises_when_client_not_found(self):
        gateway, _, _ = _make_gateway()
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_payment_approved(
                client_id=uuid4(),
                provider_id=uuid4(),
                service_request_id=uuid4(),
                payment_amount=Decimal("100.00"),
                payment_approved_at=datetime.utcnow(),
            )

    def test_notify_payment_approved_raises_when_provider_not_found(self):
        email_sender = MagicMock()
        user_repo = MagicMock()
        client = MagicMock()
        client.email = "client@example.com"
        client.name = "Cliente"
        provider_id = uuid4()
        client_id = uuid4()

        def find_user(uid):
            if uid == client_id:
                return client
            return None

        user_repo.find_user_by_id.side_effect = find_user
        gateway = EmailServiceRequestNotificationGateway(
            email_sender=email_sender,
            user_repository=user_repo,
        )
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_payment_approved(
                client_id=client_id,
                provider_id=provider_id,
                service_request_id=uuid4(),
                payment_amount=Decimal("100.00"),
                payment_approved_at=datetime.utcnow(),
            )

    def test_notify_payment_refused_raises_when_client_not_found(self):
        gateway, _, _ = _make_gateway()
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_payment_refused(
                client_id=uuid4(),
                provider_id=uuid4(),
                service_request_id=uuid4(),
                payment_amount=Decimal("100.00"),
                payment_refused_at=datetime.utcnow(),
            )

    def test_notify_payment_refused_raises_when_provider_not_found(self):
        email_sender = MagicMock()
        user_repo = MagicMock()
        client = MagicMock()
        client.email = "client@example.com"
        client.name = "Cliente"
        provider_id = uuid4()
        client_id = uuid4()

        def find_user(uid):
            if uid == client_id:
                return client
            return None

        user_repo.find_user_by_id.side_effect = find_user
        gateway = EmailServiceRequestNotificationGateway(
            email_sender=email_sender,
            user_repository=user_repo,
        )
        with pytest.raises(EmailDeliveryError, match="não encontrado"):
            gateway.notify_payment_refused(
                client_id=client_id,
                provider_id=provider_id,
                service_request_id=uuid4(),
                payment_amount=Decimal("100.00"),
                payment_refused_at=datetime.utcnow(),
            )