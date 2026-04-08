from datetime import datetime
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