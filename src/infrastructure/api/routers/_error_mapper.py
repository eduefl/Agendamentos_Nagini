from domain.service_request.service_request_exceptions import (
    InvalidServiceRequestDateError,
    ProviderDoesNotServeThisRequestError,
    ServiceRequestAddressEmptyError,
    ServiceRequestAlreadyFinishedError,
    ServiceRequestArrivalAlreadyConfirmedError,
    ServiceRequestArrivalAlreadyReportedError,
    ServiceRequestDepartureAddressEmptyError,
    ServiceRequestExpiredError,
    ServiceRequestInvalidFinalAmountError,
    ServiceRequestNotArrivedError,
    ServiceRequestNotConfirmedError,
    ServiceRequestNotFoundError,
    ServiceRequestNotInProgressError,
    ServiceRequestNotInTransitError,
    ServiceRequestProviderArrivalNotRegisteredError,
    ServiceRequestUnavailableError,
)
from domain.__seedwork.exceptions import ForbiddenError, ValidationError
from domain.service.service_exceptions import (
    ProviderServiceAlreadyActiveError,
    ProviderServiceAlreadyExistsError,
    ProviderServiceAlreadyInactiveError,
    ProviderServiceNotFoundError,
    ServiceNotFoundError,
)
from domain.security.security_exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
)
from fastapi import HTTPException, status
from domain.user.user_exceptions import (
    ActivationCodeExpiredError,
    EmailAlreadyExistsError,
    InvalidActivationCodeError,
    InvalidCredentialsError,
    RoleNotFoundError,
    RolesRequiredError,
    UserAlreadyActiveError,
    UserNotFoundError,
)
from domain.task.task_exceptions import TaskNotFoundError


def raise_http_from_error(e: Exception) -> None:
    if isinstance(e, HTTPException):
        raise e
    if isinstance(e, (InvalidCredentialsError, ExpiredTokenError, InvalidTokenError)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    if isinstance(e, ForbiddenError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if isinstance(
        e,
        (
            UserNotFoundError,
            TaskNotFoundError,
            ServiceNotFoundError,
            ProviderServiceNotFoundError,
            ServiceRequestNotFoundError,
        ),
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(
        e,
        (
            UserAlreadyActiveError,
            EmailAlreadyExistsError,
            ProviderServiceAlreadyExistsError,
            ProviderServiceAlreadyInactiveError,
            ProviderServiceAlreadyActiveError,
            ServiceRequestUnavailableError,
            ServiceRequestNotConfirmedError,
            ServiceRequestAddressEmptyError,
            ServiceRequestDepartureAddressEmptyError,
            ServiceRequestExpiredError,
            ServiceRequestNotInTransitError,
            ServiceRequestArrivalAlreadyReportedError,
            ServiceRequestNotArrivedError,
            ServiceRequestArrivalAlreadyConfirmedError,
            ServiceRequestProviderArrivalNotRegisteredError,
            ServiceRequestNotInProgressError,
            ServiceRequestAlreadyFinishedError,
            ServiceRequestInvalidFinalAmountError,
        ),
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if isinstance(e, ActivationCodeExpiredError):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    if isinstance(e, (InvalidActivationCodeError, RoleNotFoundError)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if isinstance(
        e,
        (
            ValueError,
            RolesRequiredError,
            InvalidServiceRequestDateError,
            ProviderDoesNotServeThisRequestError,
            ValidationError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )  # 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    )


# status code
# https://fastapi.tiangolo.com/pt/reference/status/#fastapi.status.WS_1015_TLS_HANDSHAKE