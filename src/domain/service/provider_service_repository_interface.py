from abc import ABC, abstractmethod
from uuid import UUID

from domain.service.provider_service_list_item_read_model import ProviderServiceListItem
from domain.service.provider_service_entity import ProviderService
from typing import Optional


class ProviderServiceRepositoryInterface(ABC):
    @abstractmethod
    def create_provider_service(self, provider_service: ProviderService) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_provider_and_service(
        self,
        provider_id: UUID,
        service_id: UUID,
    ) -> Optional[ProviderService]:
        raise NotImplementedError

    @abstractmethod
    def list_by_provider_id(self, provider_id: UUID) -> list[ProviderServiceListItem]:
        raise NotImplementedError
