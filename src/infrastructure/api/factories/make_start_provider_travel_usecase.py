from sqlalchemy.orm import Session

from infrastructure.logistics.mock_logistics_acl_gateway import MockLogisticsAclGateway
from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)
from infrastructure.notification.smtp_email_sender import SMTPEmailSender
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.start_provider_travel.start_provider_travel_usecase import (
    StartProviderTravelUseCase,
)


def make_start_provider_travel_usecase(session: Session) -> StartProviderTravelUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    logistics_acl_gateway = MockLogisticsAclGateway()
    email_sender = SMTPEmailSender()
    user_repo = userRepository(session=session)
    notification_gateway = EmailServiceRequestNotificationGateway(
        email_sender=email_sender,
        user_repository=user_repo,
    )

    return StartProviderTravelUseCase(
        service_request_repository=service_request_repository,
        logistics_acl_gateway=logistics_acl_gateway,
        notification_gateway=notification_gateway,
    )