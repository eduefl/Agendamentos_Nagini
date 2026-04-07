
"""
Testes unitários do MockLogisticsAclGateway.

Cobre:
- Retorna estrutura RouteEstimateDTO esperada
- Calcula ETA corretamente (departure_at + duration)
- Comportamento é determinístico (mesmo input → mesmo output)
- Mock configurável funciona corretamente
- Valores padrão são os esperados
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from domain.logistics.route_estimate_dto import RouteEstimateDTO
from infrastructure.logistics.mock_logistics_acl_gateway import MockLogisticsAclGateway


class TestMockLogisticsAclGateway:
    def test_returns_route_estimate_dto(self):
        gateway = MockLogisticsAclGateway()
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route(
            origin_address="Av. Paulista, 1000",
            destination_address="Rua das Flores, 123",
            departure_at=departure,
        )
        assert isinstance(result, RouteEstimateDTO)

    def test_default_duration_is_25_minutes(self):
        gateway = MockLogisticsAclGateway()
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route(
            origin_address="any",
            destination_address="any",
            departure_at=departure,
        )
        assert result.duration_minutes == 25

    def test_default_distance_is_8_5_km(self):
        gateway = MockLogisticsAclGateway()
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route(
            origin_address="any",
            destination_address="any",
            departure_at=departure,
        )
        assert result.distance_km == Decimal("8.5")

    def test_calculates_eta_correctly(self):
        gateway = MockLogisticsAclGateway(duration_minutes=25)
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route(
            origin_address="any",
            destination_address="any",
            departure_at=departure,
        )
        expected_arrival = departure + timedelta(minutes=25)
        assert result.estimated_arrival_at == expected_arrival

    def test_is_deterministic_same_departure(self):
        gateway = MockLogisticsAclGateway()
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result1 = gateway.estimate_route("A", "B", departure)
        result2 = gateway.estimate_route("A", "B", departure)
        assert result1.duration_minutes == result2.duration_minutes
        assert result1.distance_km == result2.distance_km
        assert result1.estimated_arrival_at == result2.estimated_arrival_at

    def test_is_deterministic_different_addresses(self):
        """Mock ignora endereços — resposta é sempre a mesma para o mesmo departure."""
        gateway = MockLogisticsAclGateway()
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result1 = gateway.estimate_route("Centro, SP", "Bairro X", departure)
        result2 = gateway.estimate_route("Bairro Y", "Zona Sul", departure)
        assert result1.duration_minutes == result2.duration_minutes
        assert result1.estimated_arrival_at == result2.estimated_arrival_at

    def test_configurable_duration(self):
        gateway = MockLogisticsAclGateway(duration_minutes=45)
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route("any", "any", departure)
        assert result.duration_minutes == 45
        assert result.estimated_arrival_at == departure + timedelta(minutes=45)

    def test_configurable_distance(self):
        gateway = MockLogisticsAclGateway(distance_km=Decimal("15.0"))
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route("any", "any", departure)
        assert result.distance_km == Decimal("15.0")

    def test_configurable_reference(self):
        gateway = MockLogisticsAclGateway(reference="test-ref-123")
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route("any", "any", departure)
        assert result.reference == "test-ref-123"

    def test_distance_can_be_none(self):
        gateway = MockLogisticsAclGateway(distance_km=None)
        departure = datetime(2026, 4, 7, 10, 0, 0)
        result = gateway.estimate_route("any", "any", departure)
        assert result.distance_km is None

    def test_eta_advances_with_later_departure(self):
        gateway = MockLogisticsAclGateway(duration_minutes=30)
        departure_early = datetime(2026, 4, 7, 8, 0, 0)
        departure_late = datetime(2026, 4, 7, 10, 0, 0)
        result_early = gateway.estimate_route("any", "any", departure_early)
        result_late = gateway.estimate_route("any", "any", departure_late)
        assert result_late.estimated_arrival_at > result_early.estimated_arrival_at
