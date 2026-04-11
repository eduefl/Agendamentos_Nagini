
from sqlalchemy.orm import Session

from infrastructure.payment.mock.mock_payment_acl_gateway import MockPaymentAclGateway
from infrastructure.payment.sqlalchemy.payment_attempt_repository import (
    PaymentAttemptRepository,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from usecases.service_request.apply_payment_result.apply_payment_result_usecase import (
    ApplyPaymentResultUseCase,
)
from usecases.service_request.confirm_payment.confirm_payment_usecase import (
    ConfirmPaymentUseCase,
)


def make_confirm_payment_usecase(session: Session) -> ConfirmPaymentUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    payment_attempt_repository = PaymentAttemptRepository(session=session)
    payment_acl_gateway = MockPaymentAclGateway()
    apply_payment_result_usecase = ApplyPaymentResultUseCase(
        service_request_repository=service_request_repository,
        payment_attempt_repository=payment_attempt_repository,
    )
    return ConfirmPaymentUseCase(
        service_request_repository=service_request_repository,
        payment_attempt_repository=payment_attempt_repository,
        payment_acl_gateway=payment_acl_gateway,
        apply_payment_result_usecase=apply_payment_result_usecase,
    )
