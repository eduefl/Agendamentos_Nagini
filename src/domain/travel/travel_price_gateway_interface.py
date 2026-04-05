from abc import ABC, abstractmethod
from decimal import Decimal


class TravelPriceGatewayInterface(ABC):
    @abstractmethod
    def calculate_price(
        self,
        departure_address: str,
        destination_address: str,
    ) -> Decimal:
        raise NotImplementedError
