from datetime import datetime
from typing import Optional
from uuid import UUID

from infrastructure.api.factories.make_report_provider_arrival_usecase import make_report_provider_arrival_usecase
from usecases.service_request.report_provider_arrival.report_provider_arrival_dto import ReportProviderArrivalInputDTO, ReportProviderArrivalOutputDTO
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.factories.make_list_my_confirmed_schedule_usecase import (
    make_list_my_confirmed_schedule_usecase,
)
from infrastructure.api.factories.make_start_provider_travel_usecase import (
    make_start_provider_travel_usecase,
)
from infrastructure.api.routers._error_mapper import raise_http_from_error
from infrastructure.api.security.require_prestador import require_prestador
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_dto import (
    ListMyConfirmedScheduleInputDTO,
    ListMyConfirmedScheduleOutputItemDTO,
)
from usecases.service_request.start_provider_travel.start_provider_travel_dto import (
    StartProviderTravelInputDTO,
    StartProviderTravelOutputDTO,
)
router = APIRouter(prefix="/provider-schedule", tags=["Provider Schedule"])


@router.get(
    "/me",
    response_model=list[ListMyConfirmedScheduleOutputItemDTO],
    status_code=status.HTTP_200_OK,
)
def list_my_confirmed_schedule(
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_list_my_confirmed_schedule_usecase(session)

        input_dto = ListMyConfirmedScheduleInputDTO(
            provider_id=current_user.id,
            start=start,
            end=end,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)

@router.patch(
    "/{service_request_id}/start-travel",
    response_model=StartProviderTravelOutputDTO,
    status_code=status.HTTP_200_OK,
)
def start_travel(
    service_request_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_start_provider_travel_usecase(session)

        input_dto = StartProviderTravelInputDTO(
            authenticated_user_id=current_user.id,
            service_request_id=service_request_id,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:        
        raise_http_from_error(e)






@router.patch(
    "/{service_request_id}/arrive",
    response_model=ReportProviderArrivalOutputDTO,
    status_code=status.HTTP_200_OK,
)
def report_provider_arrival(
    service_request_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_report_provider_arrival_usecase(session)


        input_dto = ReportProviderArrivalInputDTO(
            authenticated_user_id=current_user.id,
            service_request_id=service_request_id,
        )


        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)        