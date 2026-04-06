from sqlalchemy.orm import Session

from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_usecase import (
    ListMyConfirmedScheduleUseCase,
)


def make_list_my_confirmed_schedule_usecase(
    session: Session,
) -> ListMyConfirmedScheduleUseCase:
    service_request_repository = ServiceRequestRepository(session=session)
    user_repository = userRepository(session=session)

    return ListMyConfirmedScheduleUseCase(
        service_request_repository=service_request_repository,
        user_repository=user_repository,
    )