from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.service_request.client_service_list_item_read_model import (
    ClientServiceRequestListItem,
)
from domain.service_request.service_request_entity import ServiceRequest


class ServiceRequestRepositoryInterface(ABC):
    @abstractmethod
    def create(self, service_request: ServiceRequest) -> ServiceRequest:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(
        self,
        service_request_id: UUID,
    ) -> Optional[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def list_by_client_id(
        self,
        client_id: UUID,
    ) -> list[ServiceRequest]:
        raise NotImplementedError

    @abstractmethod
    def list_by_client_id_with_service_data(
        self,
        client_id: UUID,
    ) -> list[ClientServiceRequestListItem]:
        raise NotImplementedError
    
    @abstractmethod
    def update(self, service_request: ServiceRequest) -> ServiceRequest:
        raise NotImplementedError
