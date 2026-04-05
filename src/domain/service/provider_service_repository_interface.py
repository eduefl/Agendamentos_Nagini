from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.service.eligible_provider_read_model import EligibleProviderReadModel
from domain.service.provider_service_entity import ProviderService
from domain.service.provider_service_list_item_read_model import ProviderServiceListItem


class ProviderServiceRepositoryInterface(ABC):
    @abstractmethod
    def create_provider_service(self, provider_service: ProviderService) -> ProviderService:
        raise NotImplementedError

    @abstractmethod
    def find_by_provider_and_service(
        self,
        provider_id: UUID,
        service_id: UUID,
    ) -> Optional[ProviderService]:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, provider_service_id: UUID) -> Optional[ProviderService]:
        raise NotImplementedError

    @abstractmethod
    def update(self, provider_service: ProviderService) -> ProviderService:
        raise NotImplementedError

    @abstractmethod
    def list_by_provider_id(self, provider_id: UUID) -> list[ProviderServiceListItem]:
        raise NotImplementedError
    
    @abstractmethod
    def list_eligible_providers_by_service_id(
        self, service_id: UUID
    ) -> list[EligibleProviderReadModel]:
        raise NotImplementedError

    @abstractmethod
    def find_active_by_provider_and_service(
        self,
        provider_id: UUID,
        service_id: UUID,
    ) -> Optional[ProviderService]:
        raise NotImplementedError