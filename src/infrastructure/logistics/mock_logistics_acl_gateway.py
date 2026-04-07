from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from domain.logistics.logistics_acl_gateway_interface import LogisticsAclGatewayInterface
from domain.logistics.route_estimate_dto import RouteEstimateDTO

_DEFAULT_DURATION_MINUTES = 25
_DEFAULT_DISTANCE_KM = Decimal("8.5")
_DEFAULT_REFERENCE = "mock-logistics-ref"


class MockLogisticsAclGateway(LogisticsAclGatewayInterface):
    """
    Mock determinístico da ACL Logística.
    Permite configurar os valores de retorno via construtor para facilitar
    o controle em testes. Se não configurado, retorna valores fixos padrão.
    """

    def __init__(
        self,
        duration_minutes: int = _DEFAULT_DURATION_MINUTES,
        distance_km: Optional[Decimal] = _DEFAULT_DISTANCE_KM,
        reference: Optional[str] = _DEFAULT_REFERENCE,
    ):
        self._duration_minutes = duration_minutes
        self._distance_km = distance_km
        self._reference = reference

    def estimate_route(
        self,
        origin_address: str,
        destination_address: str,
        departure_at: datetime,
    ) -> RouteEstimateDTO:
        estimated_arrival_at = departure_at + timedelta(minutes=self._duration_minutes)
        return RouteEstimateDTO(
            duration_minutes=self._duration_minutes,
            distance_km=self._distance_km,
            estimated_arrival_at=estimated_arrival_at,
            reference=self._reference,
        )