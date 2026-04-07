from abc import ABC, abstractmethod
from datetime import datetime

from domain.logistics.route_estimate_dto import RouteEstimateDTO


class LogisticsAclGatewayInterface(ABC):
    @abstractmethod
    def estimate_route(
        self,
        origin_address: str,
        destination_address: str,
        departure_at: datetime,
    ) -> RouteEstimateDTO:
        raise NotImplementedError