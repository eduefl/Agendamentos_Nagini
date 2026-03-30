from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.routers._error_mapper import raise_http_from_error
from infrastructure.api.security.require_prestador import require_prestador
from infrastructure.api.factories.make_create_provider_service_usecase import make_create_provider_service_usecase
from usecases.service.create_provider_service.create_provider_service_dto import (
    CreateProviderServiceInputDTO,
    CreateProviderServiceOutputDTO,
)

from infrastructure.api.routers.dto.service_routers_dto import CreateProviderServiceRequestDTO

router = APIRouter(prefix="/provider-services", tags=["Provider Services"])




@router.post(
    "/",
    response_model=CreateProviderServiceOutputDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_provider_service(
    request: CreateProviderServiceRequestDTO,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_create_provider_service_usecase(session)

        input_dto = CreateProviderServiceInputDTO(
            provider_id=current_user.id,
            name=request.name,
            service_id=request.service_id,
            description=request.description,
            price=request.price,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)
