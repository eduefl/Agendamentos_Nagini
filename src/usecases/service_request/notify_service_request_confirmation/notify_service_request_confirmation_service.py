from domain.notification.email_sender_interface import EmailSenderInterface
from domain.service.service_repository_interface import ServiceRepositoryInterface
from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from domain.user.user_repository_interface import userRepositoryInterface


class NotifyServiceRequestConfirmationService:
    def __init__(
        self,
        email_sender: EmailSenderInterface,
        user_repository: userRepositoryInterface,
        service_repository: ServiceRepositoryInterface,
    ):
        self._email_sender = email_sender
        self._user_repository = user_repository
        self._service_repository = service_repository

    def notify(self, service_request: ServiceRequest) -> None:
        if service_request.status != ServiceRequestStatus.CONFIRMED.value:
            raise ValueError(
                "Cannot notify: service request is not in CONFIRMED status."
            )

        client = self._user_repository.find_user_by_id(service_request.client_id)
        provider = self._user_repository.find_user_by_id(service_request.accepted_provider_id)
        service = self._service_repository.find_by_id(service_request.service_id)

        self._email_sender.send_service_request_confirmed_to_client(
            client_email=client.email,
            client_name=client.name,
            service_name=service.name,
            service_price=service_request.service_price,
            travel_price=service_request.travel_price,
            total_price=service_request.total_price,
            status=service_request.status,
        )

        self._email_sender.send_service_request_confirmed_to_provider(
            provider_email=provider.email,
            provider_name=provider.name,
            service_name=service.name,
            service_price=service_request.service_price,
            service_address=service_request.address,
            travel_price=service_request.travel_price,
            total_price=service_request.total_price,
        )