from domain.__seedwork.normalize import normalize_service_name
from usecases.service.list_services.list_services_dto import ListServicesInputDTO, ListServicesOutputItemDTO
from domain.service.service_repository_interface import ServiceRepositoryInterface


class ListServicesUseCase:
    def __init__(self, service_repository: ServiceRepositoryInterface):
        self.service_repository = service_repository

    def execute(self, input: ListServicesInputDTO) -> list[ListServicesOutputItemDTO]:
        services = self.service_repository.list_all()

        return [
            ListServicesOutputItemDTO(
                service_id=service.id,
                name=normalize_service_name(service.name),
                description=service.description,
            )
            for service in services
        ]

