"""
Unit tests for SMTPEmailSender.
Tests success paths (with mocked SMTP) and failure paths (missing env vars / SMTP errors).
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from domain.notification.notification_exceptions import EmailDeliveryError
from infrastructure.notification.smtp_email_sender import SMTPEmailSender


ENV_VARS = {
    "EMAIL_SENDER_ADDRESS": "sender@example.com",
    "EMAIL_SENDER_PASSWORD": "secret",
}


def _mock_smtp():
    smtp_instance = MagicMock()
    smtp_instance.__enter__ = lambda s: s
    smtp_instance.__exit__ = MagicMock(return_value=False)
    return smtp_instance


class TestSendActivationEmail:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_activation_email(to_email="user@example.com", activation_code="123456")
        smtp_mock.login.assert_called_once_with("sender@example.com", "secret")
        smtp_mock.send_message.assert_called_once()

    def test_raises_email_delivery_error_on_failure(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_activation_email(to_email="user@example.com", activation_code="abc")


class TestSendServiceRequestNotificationEmail:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_service_request_notification_email(
                to_email="provider@example.com",
                provider_name="João",
                service_name="Pintura",
                desired_datetime=now,
                address="Rua A, 1",
                expires_at=now,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_email_delivery_error_on_failure(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_service_request_notification_email(
                    to_email="p@example.com",
                    provider_name="P",
                    service_name="S",
                    desired_datetime=datetime.utcnow(),
                    address=None,
                    expires_at=None,
                )


class TestSendServiceRequestConfirmedToClient:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_service_request_confirmed_to_client(
                client_email="c@example.com",
                client_name="Maria",
                service_name="Pintura",
                service_price=Decimal("100.00"),
                travel_price=Decimal("20.00"),
                total_price=Decimal("120.00"),
                status="CONFIRMED",
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_smtp_failure(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_service_request_confirmed_to_client(
                    client_email="c@example.com",
                    client_name="M",
                    service_name="S",
                    service_price=Decimal("100.00"),
                    travel_price=Decimal("20.00"),
                    total_price=Decimal("120.00"),
                    status="CONFIRMED",
                )


class TestSendServiceRequestConfirmedToProvider:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_service_request_confirmed_to_provider(
                provider_email="p@example.com",
                provider_name="João",
                service_name="Pintura",
                service_price=Decimal("100.00"),
                service_address="Rua B, 2",
                travel_price=Decimal("20.00"),
                total_price=Decimal("120.00"),
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_smtp_failure(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_service_request_confirmed_to_provider(
                    provider_email="p@example.com",
                    provider_name="J",
                    service_name="S",
                    service_price=Decimal("100.00"),
                    service_address=None,
                    travel_price=Decimal("20.00"),
                    total_price=Decimal("120.00"),
                )


class TestSendTravelStartedToClient:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_travel_started_to_client(
                client_email="c@example.com",
                client_name="Ana",
                estimated_arrival_at=now,
                travel_duration_minutes=30,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_travel_started_to_client(
                    client_email="c@example.com",
                    client_name="A",
                    estimated_arrival_at=datetime.utcnow(),
                    travel_duration_minutes=15,
                )


class TestSendProviderArrivedToClient:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_provider_arrived_to_client(
                client_email="c@example.com",
                client_name="Carlos",
                provider_arrived_at=now,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_provider_arrived_to_client(
                    client_email="c@example.com",
                    client_name="C",
                    provider_arrived_at=datetime.utcnow(),
                )


class TestSendPaymentRequestedToClient:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_payment_requested_to_client(
                client_email="c@example.com",
                client_name="Lucia",
                payment_amount=Decimal("150.00"),
                payment_requested_at=now,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_payment_requested_to_client(
                    client_email="c@example.com",
                    client_name="L",
                    payment_amount=Decimal("100.00"),
                    payment_requested_at=datetime.utcnow(),
                )


class TestSendPaymentApprovedToClient:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_payment_approved_to_client(
                client_email="c@example.com",
                client_name="Bia",
                payment_amount=Decimal("200.00"),
                payment_approved_at=now,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_payment_approved_to_client(
                    client_email="c@example.com",
                    client_name="B",
                    payment_amount=Decimal("200.00"),
                    payment_approved_at=datetime.utcnow(),
                )


class TestSendPaymentApprovedToProvider:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_payment_approved_to_provider(
                provider_email="p@example.com",
                provider_name="Pedro",
                payment_amount=Decimal("200.00"),
                payment_approved_at=now,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_payment_approved_to_provider(
                    provider_email="p@example.com",
                    provider_name="P",
                    payment_amount=Decimal("200.00"),
                    payment_approved_at=datetime.utcnow(),
                )


class TestSendPaymentRefusedToClient:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_payment_refused_to_client(
                client_email="c@example.com",
                client_name="Clara",
                payment_amount=Decimal("100.00"),
                payment_refused_at=now,
                refusal_reason="Saldo insuficiente",
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_payment_refused_to_client(
                    client_email="c@example.com",
                    client_name="C",
                    payment_amount=Decimal("100.00"),
                    payment_refused_at=datetime.utcnow(),
                )


class TestSendPaymentRefusedToProvider:
    def test_success(self):
        sender = SMTPEmailSender()
        smtp_mock = _mock_smtp()
        now = datetime.utcnow()
        with patch.dict("os.environ", ENV_VARS), patch(
            "smtplib.SMTP_SSL", return_value=smtp_mock
        ):
            sender.send_payment_refused_to_provider(
                provider_email="p@example.com",
                provider_name="Roberto",
                payment_amount=Decimal("100.00"),
                payment_refused_at=now,
            )
        smtp_mock.send_message.assert_called_once()

    def test_raises_on_missing_env_vars(self):
        sender = SMTPEmailSender()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EmailDeliveryError):
                sender.send_payment_refused_to_provider(
                    provider_email="p@example.com",
                    provider_name="R",
                    payment_amount=Decimal("100.00"),
                    payment_refused_at=datetime.utcnow(),
                )