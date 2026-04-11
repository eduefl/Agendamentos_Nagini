
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
        self.provider_arrived_notifications_sent = []
        self.payment_requested_notifications_sent = []
        self.payment_approved_client_notifications_sent = []
        self.payment_approved_provider_notifications_sent = []
        self.payment_refused_client_notifications_sent = []
        self.payment_refused_provider_notifications_sent = []
        
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

    def send_provider_arrived_to_client(
        self,
        client_email: str,
        client_name: str,
        provider_arrived_at: datetime,
    ) -> None:
        self.provider_arrived_notifications_sent.append(
            {
                "client_email": client_email,
                "client_name": client_name,
                "provider_arrived_at": provider_arrived_at,
            }
        )

    def send_payment_requested_to_client(
        self,
        client_email: str,
        client_name: str,
        payment_amount: Decimal,
        payment_requested_at: datetime,
    ) -> None:
        self.payment_requested_notifications_sent.append(
            {
                "client_email": client_email,
                "client_name": client_name,
                "payment_amount": payment_amount,
                "payment_requested_at": payment_requested_at,
            }
        )

    def send_payment_approved_to_client(
        self,
        client_email: str,
        client_name: str,
        payment_amount: Decimal,
        payment_approved_at: datetime,
    ) -> None:
        self.payment_approved_client_notifications_sent.append(
            {
                "client_email": client_email,
                "client_name": client_name,
                "payment_amount": payment_amount,
                "payment_approved_at": payment_approved_at,
            }
        )

    def send_payment_approved_to_provider(
        self,
        provider_email: str,
        provider_name: str,
        payment_amount: Decimal,
        payment_approved_at: datetime,
    ) -> None:
        self.payment_approved_provider_notifications_sent.append(
            {
                "provider_email": provider_email,
                "provider_name": provider_name,
                "payment_amount": payment_amount,
                "payment_approved_at": payment_approved_at,
            }
        )

    def send_payment_refused_to_client(
        self,
        client_email: str,
        client_name: str,
        payment_amount: Decimal,
        payment_refused_at: datetime,
        refusal_reason: Optional[str] = None,
    ) -> None:
        self.payment_refused_client_notifications_sent.append(
            {
                "client_email": client_email,
                "client_name": client_name,
                "payment_amount": payment_amount,
                "payment_refused_at": payment_refused_at,
                "refusal_reason": refusal_reason,
            }
        )

    def send_payment_refused_to_provider(
        self,
        provider_email: str,
        provider_name: str,
        payment_amount: Decimal,
        payment_refused_at: datetime,
    ) -> None:
        self.payment_refused_provider_notifications_sent.append(
            {
                "provider_email": provider_email,
                "provider_name": provider_name,
                "payment_amount": payment_amount,
                "payment_refused_at": payment_refused_at,
            }
        )   