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
                name=self._normalize_name(service.name),
                description=service.description,
            )
            for service in services
        ]

    @staticmethod
    def _normalize_name(name: str) -> str:
        lower_words = {"de", "da", "do", "das", "dos", "e"}
        words = name.strip().lower().split()

        formatted = [
            word.capitalize() if index == 0 or word not in lower_words else word
            for index, word in enumerate(words)
        ]

        return " ".join(formatted)
