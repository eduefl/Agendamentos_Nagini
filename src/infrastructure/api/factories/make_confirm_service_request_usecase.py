from sqlalchemy.orm import Session

from infrastructure.notification.smtp_email_sender import SMTPEmailSender
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.travel.mock_travel_price_gateway import MockTravelPriceGateway
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.confirm_service_request.confirm_service_request_usecase import (
    ConfirmServiceRequestUseCase,
)
from usecases.service_request.notify_service_request_confirmation.notify_service_request_confirmation_service import (
    NotifyServiceRequestConfirmationService,
)


def make_confirm_service_request_usecase(session: Session) -> ConfirmServiceRequestUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    provider_service_repository = ProviderServiceRepository(session=session)
    travel_price_gateway = MockTravelPriceGateway()
    email_sender = SMTPEmailSender()
    user_repository = userRepository(session=session)
    service_repository = ServiceRepository(session=session)

    notification_service = NotifyServiceRequestConfirmationService(
        email_sender=email_sender,
        user_repository=user_repository,
        service_repository=service_repository,
    )

    return ConfirmServiceRequestUseCase(
        service_request_repository=service_request_repository,
        provider_service_repository=provider_service_repository,
        travel_price_gateway=travel_price_gateway,
        notification_service=notification_service,
    )