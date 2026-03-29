from abc import ABC, abstractmethod
from uuid import UUID

from domain.service.provider_service_entity import ProviderService


class ProviderServiceRepositoryInterface(ABC):
    @abstractmethod
    def find_by_provider_and_service(
        self,
        provider_id: UUID,
        service_id: UUID,
    ) -> ProviderService | None:
        raise NotImplementedError

    @abstractmethod
    def add(self, provider_service: ProviderService) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_by_provider_id(self, provider_id: UUID) -> list[ProviderService]:
        raise NotImplementedError
