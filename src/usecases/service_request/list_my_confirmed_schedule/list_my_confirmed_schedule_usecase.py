from domain.__seedwork.exceptions import ForbiddenError, ValidationError
from domain.user.user_repository_interface import userRepositoryInterface
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_dto import (
    ListMyConfirmedScheduleInputDTO,
    ListMyConfirmedScheduleOutputItemDTO,
)


class ListMyConfirmedScheduleUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        user_repository: userRepositoryInterface,
    ):
        self.service_request_repository = service_request_repository
        self._user_repository = user_repository

    def execute(
        self,
        input_dto: ListMyConfirmedScheduleInputDTO,
    ) -> list[ListMyConfirmedScheduleOutputItemDTO]:

        user = self._user_repository.find_user_by_id(input_dto.provider_id)

        if not user.is_active:
            raise ForbiddenError("Usuário inativo não pode acessar esta operação")

        if not user.is_provider():
            raise ForbiddenError(
                "Apenas usuários com perfil prestador podem acessar esta operação"
            )

        if input_dto.start is not None and input_dto.end is not None:
            if input_dto.start > input_dto.end:
                raise ValidationError("start deve ser menor ou igual a end")

        items = self.service_request_repository.list_operational_schedule_for_provider(
            provider_id=input_dto.provider_id,
            start=input_dto.start,
            end=input_dto.end,
        )

        return [
            ListMyConfirmedScheduleOutputItemDTO(
                service_request_id=item.service_request_id,
                service_id=item.service_id,
                service_name=item.service_name,
                service_description=item.service_description,
                client_id=item.client_id,
                desired_datetime=item.desired_datetime,
                address=item.address,
                status=item.status,
                service_price=item.service_price,
                travel_price=item.travel_price,
                total_price=item.total_price,
                accepted_at=item.accepted_at,
                travel_started_at=item.travel_started_at,
                estimated_arrival_at=item.estimated_arrival_at,
                travel_duration_minutes=item.travel_duration_minutes,
                provider_arrived_at=item.provider_arrived_at,
                service_started_at=item.service_started_at,
            )
            for item in items
        ]
