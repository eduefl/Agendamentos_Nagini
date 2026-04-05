from datetime import datetime
from typing import Optional
from uuid import UUID

from infrastructure.api.factories.make_confirm_service_request_usecase import make_confirm_service_request_usecase
from infrastructure.api.factories.make_list_my_service_requests_usecase import make_list_my_service_requests_usecase
from usecases.service_request.confirm_service_request.confirm_service_request_dto import ConfirmServiceRequestInputDTO, ConfirmServiceRequestOutputDTO
from usecases.service_request.list_my_service_requests.list_my_service_requests_dto import ListMyServiceRequestsInputDTO, ListMyServiceRequestsOutputItemDTO
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.security.require_cliente import require_cliente
from infrastructure.api.security.require_prestador import require_prestador

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

@router.get(
    "/me",
    response_model=list[ListMyServiceRequestsOutputItemDTO],
    status_code=status.HTTP_200_OK,
)
def list_my_service_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_cliente),
):
    try:
        use_case = make_list_my_service_requests_usecase(session)

        input_dto = ListMyServiceRequestsInputDTO(
            client_id=current_user.id,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)


class AcceptServiceRequestBody(BaseModel):
    departure_address: str


@router.patch(
    "/{service_request_id}/accept",
    response_model=ConfirmServiceRequestOutputDTO,
    status_code=status.HTTP_200_OK,
)
def accept_service_request(
    service_request_id: UUID,
    body: AcceptServiceRequestBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_confirm_service_request_usecase(session)
        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request_id,
            provider_id=current_user.id,
            departure_address=body.departure_address,
        )
        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)
