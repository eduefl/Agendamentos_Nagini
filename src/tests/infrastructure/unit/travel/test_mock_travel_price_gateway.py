from decimal import Decimal

from infrastructure.travel.mock_travel_price_gateway import MockTravelPriceGateway


class TestMockTravelPriceGateway:
    def test_calculate_price_returns_expected_value(self, monkeypatch):
        gateway = MockTravelPriceGateway()

        monkeypatch.setattr(
            "infrastructure.travel.mock_travel_price_gateway.random.randint",
            lambda a, b: 10,
        )
        monkeypatch.setattr(
            "infrastructure.travel.mock_travel_price_gateway.random.triangular",
            lambda low, high, mode: 1.0,
        )

        result = gateway.calculate_price(
            departure_address="Rua A, 123",
            destination_address="Rua B, 456",
        )

        # 10 km * 1.20 * 1.0 = 12.00
        assert result == Decimal("12.00")

    def test_calculate_price_applies_round_half_up(self, monkeypatch):
        gateway = MockTravelPriceGateway()

        monkeypatch.setattr(
            "infrastructure.travel.mock_travel_price_gateway.random.randint",
            lambda a, b: 7,
        )
        monkeypatch.setattr(
            "infrastructure.travel.mock_travel_price_gateway.random.triangular",
            lambda low, high, mode: 1.1111,
        )

        result = gateway.calculate_price(
            departure_address="Origem",
            destination_address="Destino",
        )

        # 7 * 1.20 * 1.1111 = 9.33324 -> 9.33
        assert result == Decimal("9.33")

    def test_calculate_price_uses_generated_bounds(self, monkeypatch):
        gateway = MockTravelPriceGateway()
        captured = {}

        def fake_randint(a, b):
            captured["randint_args"] = (a, b)
            return 1

        def fake_triangular(low, high, mode):
            captured["triangular_args"] = (low, high, mode)
            return 0.8

        monkeypatch.setattr(
            "infrastructure.travel.mock_travel_price_gateway.random.randint",
            fake_randint,
        )
        monkeypatch.setattr(
            "infrastructure.travel.mock_travel_price_gateway.random.triangular",
            fake_triangular,
        )

        result = gateway.calculate_price(
            departure_address="Origem",
            destination_address="Destino",
        )

        assert captured["randint_args"] == (1, 50)
        assert captured["triangular_args"] == (0.8, 1.2, 1.0)
        # 1 * 1.20 * 0.8 = 0.96
        assert result == Decimal("0.96")