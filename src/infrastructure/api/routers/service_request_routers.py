from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.security.require_cliente import require_cliente

from infrastructure.api.factories.make_create_service_request_usecase import (
    make_create_service_request_usecase,
)
from infrastructure.api.routers._error_mapper import raise_http_from_error
from usecases.service_request.create_service_request.create_service_request_dto import (
    CreateServiceRequestInputDTO,
    CreateServiceRequestOutputDTO,
)


router = APIRouter(prefix="/service-requests", tags=["service-requests"])


class CreateServiceRequestBody(BaseModel):
    service_id: UUID
    desired_datetime: datetime
    address: Optional[str] = None


@router.post(
    "/",
    response_model=CreateServiceRequestOutputDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_service_request(
    body: CreateServiceRequestBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_cliente),
):
    try:
        use_case = make_create_service_request_usecase(session)

        input_dto = CreateServiceRequestInputDTO(
            client_id=current_user.id,
            service_id=body.service_id,
            desired_datetime=body.desired_datetime,
            address=body.address,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)
