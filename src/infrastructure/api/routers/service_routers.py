from infrastructure.api.factories.make_list_services_usecase import (
    make_list_services_usecase,
)
from infrastructure.api.security.get_current_user import get_current_user
from usecases.service.list_services.list_services_dto import ListServicesInputDTO, ListServicesOutputItemDTO
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.routers._error_mapper import raise_http_from_error

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/", response_model=list[ListServicesOutputItemDTO])
def list_services(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        usecase = make_list_services_usecase(session)
        return usecase.execute(input=ListServicesInputDTO())
    except Exception as e:
        raise_http_from_error(e)
