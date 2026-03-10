from fastapi import HTTPException, status
from domain.user.user_exceptions import UserNotFoundError
from domain.task.task_exceptions import TaskNotFoundError

def raise_http_from_error(e: Exception) -> None:
    if isinstance(e, HTTPException):
        raise e
    if isinstance(e, UserNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, TaskNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
