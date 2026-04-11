from sqlalchemy.orm import Session

from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)
from infrastructure.notification.smtp_email_sender import SMTPEmailSender
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.finish_service_and_request_payment.finish_service_and_request_payment_usecase import (
    FinishServiceAndRequestPaymentUseCase,
)


def make_finish_service_and_request_payment_usecase(
    session: Session,
) -> FinishServiceAndRequestPaymentUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    email_sender = SMTPEmailSender()
    user_repo = userRepository(session=session)
    notification_gateway = EmailServiceRequestNotificationGateway(
        email_sender=email_sender,
        user_repository=user_repo,
    )

    return FinishServiceAndRequestPaymentUseCase(
        service_request_repository=service_request_repository,
        notification_gateway=notification_gateway,
    )