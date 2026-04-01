from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.service.service_entity import Service


class ServiceRepositoryInterface(ABC):

    @abstractmethod
    def create_service(self, service: Service) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, service_id: UUID) -> Service:
        raise NotImplementedError

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Service]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Service]:
        raise NotImplementedError
