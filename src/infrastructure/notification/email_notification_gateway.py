from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.email_sender_interface import EmailSenderInterface
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
from domain.user.user_repository_interface import userRepositoryInterface


class EmailServiceRequestNotificationGateway(ServiceRequestNotificationGatewayInterface):
    """
    Implementação real do gateway de notificação de solicitações de serviço.
    Usa EmailSenderInterface para enviar emails e UserRepositoryInterface
    para buscar os dados do cliente a partir do client_id.
    """

    def __init__(
        self,
        email_sender: EmailSenderInterface,
        user_repository: userRepositoryInterface,
    ):
        self._email_sender = email_sender
        self._user_repository = user_repository

    def notify_client_travel_started(
        self,
        client_id: UUID,
        service_request_id: UUID,
        estimated_arrival_at: datetime,
        travel_duration_minutes: int,
    ) -> None:
        client = self._user_repository.find_user_by_id(client_id)
        if client is None:
            raise EmailDeliveryError(f"Cliente com ID {client_id} não encontrado")

        self._email_sender.send_travel_started_to_client(
            client_email=client.email,
            client_name=client.name,
            estimated_arrival_at=estimated_arrival_at,
            travel_duration_minutes=travel_duration_minutes,
        )

    def notify_client_provider_arrived(
        self,
        client_id: UUID,
        service_request_id: UUID,
        provider_arrived_at: datetime,
    ) -> None:
        client = self._user_repository.find_user_by_id(client_id)
        if client is None:
            raise EmailDeliveryError(f"Cliente com ID {client_id} não encontrado")

        self._email_sender.send_provider_arrived_to_client(
            client_email=client.email,
            client_name=client.name,
            provider_arrived_at=provider_arrived_at,
        )

    def notify_payment_requested(
        self,
        client_id: UUID,
        service_request_id: UUID,
        payment_amount: Decimal,
        payment_requested_at: datetime,
    ) -> None:
        client = self._user_repository.find_user_by_id(client_id)
        if client is None:
            raise EmailDeliveryError(f"Cliente com ID {client_id} não encontrado")

        self._email_sender.send_payment_requested_to_client(
            client_email=client.email,
            client_name=client.name,
            payment_amount=payment_amount,
            payment_requested_at=payment_requested_at,
        )

    def notify_payment_approved(
        self,
        client_id: UUID,
        provider_id: UUID,
        service_request_id: UUID,
        payment_amount: Decimal,
        payment_approved_at: datetime,
    ) -> None:
        client = self._user_repository.find_user_by_id(client_id)
        if client is None:
            raise EmailDeliveryError(f"Cliente com ID {client_id} não encontrado")

        provider = self._user_repository.find_user_by_id(provider_id)
        if provider is None:
            raise EmailDeliveryError(f"Prestador com ID {provider_id} não encontrado")

        self._email_sender.send_payment_approved_to_client(
            client_email=client.email,
            client_name=client.name,
            payment_amount=payment_amount,
            payment_approved_at=payment_approved_at,
        )
        self._email_sender.send_payment_approved_to_provider(
            provider_email=provider.email,
            provider_name=provider.name,
            payment_amount=payment_amount,
            payment_approved_at=payment_approved_at,
        )

    def notify_payment_refused(
        self,
        client_id: UUID,
        provider_id: UUID,
        service_request_id: UUID,
        payment_amount: Decimal,
        payment_refused_at: datetime,
        refusal_reason: Optional[str] = None,
    ) -> None:
        client = self._user_repository.find_user_by_id(client_id)
        if client is None:
            raise EmailDeliveryError(f"Cliente com ID {client_id} não encontrado")

        provider = self._user_repository.find_user_by_id(provider_id)
        if provider is None:
            raise EmailDeliveryError(f"Prestador com ID {provider_id} não encontrado")

        self._email_sender.send_payment_refused_to_client(
            client_email=client.email,
            client_name=client.name,
            payment_amount=payment_amount,
            payment_refused_at=payment_refused_at,
            refusal_reason=refusal_reason,
        )
        self._email_sender.send_payment_refused_to_provider(
            provider_email=provider.email,
            provider_name=provider.name,
            payment_amount=payment_amount,
            payment_refused_at=payment_refused_at,
        )