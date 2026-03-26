from fastapi import HTTPException, status
from domain.user.user_exceptions import ActivationCodeExpiredError, EmailAlreadyExistsError, InvalidActivationCodeError, RoleNotFoundError, RolesRequiredError, UserAlreadyActiveError, UserNotFoundError
from domain.task.task_exceptions import TaskNotFoundError

def raise_http_from_error(e: Exception) -> None:
    if isinstance(e, HTTPException):
        raise e
    if isinstance(e, (UserNotFoundError, TaskNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, (UserAlreadyActiveError, EmailAlreadyExistsError)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if isinstance(e, ActivationCodeExpiredError):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    if isinstance(e, (InvalidActivationCodeError, RoleNotFoundError)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))    
    if isinstance(e, (ValueError, RolesRequiredError)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# status code 
# https://fastapi.tiangolo.com/pt/reference/status/#fastapi.status.WS_1015_TLS_HANDSHAKE