from abc import ABC, abstractmethod
from uuid import UUID

from domain.service.service_entity import Service


class ServiceRepositoryInterface(ABC):
    @abstractmethod
    def find_by_id(self, service_id: UUID) -> Service:
        raise NotImplementedError

    @abstractmethod
    def find_by_name(self, name: str) -> Service | None:
        raise NotImplementedError

    @abstractmethod
    def add(self, service: Service) -> None:
        raise NotImplementedError
