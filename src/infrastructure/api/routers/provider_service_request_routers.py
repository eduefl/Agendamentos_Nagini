from uuid import UUID
from infrastructure.api.factories.make_list_available_service_requests_for_provider_usecase import make_list_available_service_requests_for_provider_usecase
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_dto import ListAvailableServiceRequestsForProviderInputDTO, ListAvailableServiceRequestsForProviderOutputItemDTO
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.routers._error_mapper import raise_http_from_error
from infrastructure.api.security.require_prestador import require_prestador


router = APIRouter(prefix="/provider-service-requests", tags=["Provider Service Requests"])

@router.get(
    "/available",
    response_model=list[ListAvailableServiceRequestsForProviderOutputItemDTO],
    status_code=status.HTTP_200_OK,
)
def list_available_service_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_list_available_service_requests_for_provider_usecase(session)
        input_dto = ListAvailableServiceRequestsForProviderInputDTO(
            provider_id=current_user.id,
        )
        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)
