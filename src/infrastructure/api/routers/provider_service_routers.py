from uuid import UUID
from infrastructure.api.factories.make_activate_provider_service_usecase import make_activate_provider_service_usecase
from usecases.service.activate_provider_service.activate_provider_service_dto import ActivateProviderServiceInputDTO, ActivateProviderServiceOutputDTO
from infrastructure.api.factories.make_deactivate_provider_service_usecase import (
    make_deactivate_provider_service_usecase,
)
from usecases.service.deactivate_provider_service.deactivate_provider_service_dto import (
    DeactivateProviderServiceInputDTO,
    DeactivateProviderServiceOutputDTO,
)
from infrastructure.api.factories.make_list_provider_services_usecase import (
    make_list_provider_services_usecase,
)
from usecases.service.list_provider_services.list_provider_services_dto import (
    ListProviderServicesInputDTO,
    ListProviderServicesOutputDTO,
)
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.api.routers._error_mapper import raise_http_from_error
from infrastructure.api.security.require_prestador import require_prestador
from infrastructure.api.factories.make_create_provider_service_usecase import (
    make_create_provider_service_usecase,
)
from usecases.service.create_provider_service.create_provider_service_dto import (
    CreateProviderServiceInputDTO,
    CreateProviderServiceOutputDTO,
)

from infrastructure.api.routers.dto.provider_service_routers_dto import (
    CreateProviderServiceRequestDTO,
)

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


@router.get(
    "/",
    response_model=ListProviderServicesOutputDTO,
    status_code=status.HTTP_200_OK,
)
def list_provider_services(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_list_provider_services_usecase(session)

        input_dto = ListProviderServicesInputDTO(
            provider_id=current_user.id,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)


@router.patch(
    "/{provider_service_id}/deactivate",
    response_model=DeactivateProviderServiceOutputDTO,
    status_code=status.HTTP_200_OK,
)
def deactivate_provider_service(
    provider_service_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_deactivate_provider_service_usecase(session)

        input_dto = DeactivateProviderServiceInputDTO(
            provider_id=current_user.id,
            provider_service_id=provider_service_id,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)

@router.patch(
    "/{provider_service_id}/activate",
    response_model=ActivateProviderServiceOutputDTO,
    status_code=status.HTTP_200_OK,
)
def activate_provider_service(
    provider_service_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_prestador),
):
    try:
        use_case = make_activate_provider_service_usecase(session)

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=current_user.id,
            provider_service_id=provider_service_id,
        )

        output = use_case.execute(input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)
