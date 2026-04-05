import random
from decimal import Decimal, ROUND_HALF_UP

from domain.travel.travel_price_gateway_interface import TravelPriceGatewayInterface

_PRICE_PER_KM = Decimal("1.20")
_MIN_KM = 1
_MAX_KM = 50


class MockTravelPriceGateway(TravelPriceGatewayInterface):
    def calculate_price(
        self,
        departure_address: str,
        destination_address: str,
    ) -> Decimal:
        km = Decimal(str(random.randint(_MIN_KM, _MAX_KM)))
        # Multiplicador próximo de 1 usando distribuição triangular (min=0.8, peak=1.0, max=1.2)
        factor = Decimal(str(random.triangular(0.8, 1.2, 1.0))).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        price = (km * _PRICE_PER_KM * factor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return price
