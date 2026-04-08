
from decimal import Decimal
from datetime import datetime
from typing import Optional

from domain.notification.email_sender_interface import EmailSenderInterface


class FakeEmailSender(EmailSenderInterface):
    def __init__(self):
        self.sent_emails = []
        self.client_confirmation_notifications_sent = []
        self.provider_confirmation_notifications_sent = []
        self.travel_started_notifications_sent = []

    def send_activation_email(self, to_email: str, activation_code: str) -> None:
        self.sent_emails.append((to_email, activation_code))

    def send_service_request_notification_email(
        self,
        to_email: str,
        provider_name: str,
        service_name: str,
        desired_datetime,
        address,
        expires_at,
    ) -> None:
        self.sent_emails.append(
            (
                to_email,
                provider_name,
                service_name,
                desired_datetime,
                address,
                expires_at,
            )
        )

    def send_service_request_confirmed_to_client(
        self,
        client_email: str,
        client_name: str,
        service_name: str,
        service_price: Decimal,
        travel_price: Decimal,
        total_price: Decimal,
        status: str,
    ) -> None:
        self.client_confirmation_notifications_sent.append(
            {
                "client_email": client_email,
                "client_name": client_name,
                "service_name": service_name,
                "service_price": service_price,
                "travel_price": travel_price,
                "total_price": total_price,
                "status": status,
            }
        )

    def send_service_request_confirmed_to_provider(
        self,
        provider_email: str,
        provider_name: str,
        service_name: str,
        service_price: Decimal,
        service_address: Optional[str],
        travel_price: Decimal,
        total_price: Decimal,
    ) -> None:
        self.provider_confirmation_notifications_sent.append(
            {
                "provider_email": provider_email,
                "provider_name": provider_name,
                "service_name": service_name,
                "service_price": service_price,
                "service_address": service_address,
                "travel_price": travel_price,
                "total_price": total_price,
            }
        )

    def send_travel_started_to_client(
        self,
        client_email: str,
        client_name: str,
        estimated_arrival_at: datetime,
        travel_duration_minutes: int,
    ) -> None:
        self.travel_started_notifications_sent.append(
            {
                "client_email": client_email,
                "client_name": client_name,
                "estimated_arrival_at": estimated_arrival_at,
                "travel_duration_minutes": travel_duration_minutes,
            }
        )
