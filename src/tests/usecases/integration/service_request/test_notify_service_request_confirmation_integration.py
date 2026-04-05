from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from domain.travel.travel_price_gateway_interface import TravelPriceGatewayInterface
from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel
from infrastructure.service.sqlalchemy.provider_service_repository import ProviderServiceRepository
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import ServiceRequestRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.fakes.fake_email_sender import FakeEmailSender
from usecases.service_request.confirm_service_request.confirm_service_request_dto import (
    ConfirmServiceRequestInputDTO,
)
from usecases.service_request.confirm_service_request.confirm_service_request_usecase import (
    ConfirmServiceRequestUseCase,
)
from usecases.service_request.notify_service_request_confirmation.notify_service_request_confirmation_service import (
    NotifyServiceRequestConfirmationService,
)


class DeterministicTravelPriceGateway(TravelPriceGatewayInterface):
    def __init__(self, fixed_price: Decimal):
        self.fixed_price = fixed_price

    def calculate_price(self, departure_address: str, destination_address: str) -> Decimal:
        return self.fixed_price


class TestNotifyServiceRequestConfirmationIntegration:
    @staticmethod
    def _create_user(session, make_user, roles, email=None, name=None):
        repo = userRepository(session=session)
        user = make_user(
            id=uuid4(),
            name=name or f"User {uuid4().hex[:8]}",
            email=email or f"{uuid4().hex}@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles=roles,
        )
        repo.add_user(user)
        return user

    @staticmethod
    def _create_service(session, name=None):
        service = ServiceModel(
            id=uuid4(),
            name=name or f"servico {uuid4().hex}",
            description="Descricao",
        )
        session.add(service)
        session.commit()
        return service

    @staticmethod
    def _create_provider_service(session, provider_id, service_id, price=Decimal("100.00")):
        ps = ProviderServiceModel(
            id=uuid4(),
            provider_id=provider_id,
            service_id=service_id,
            price=price,
            active=True,
        )
        session.add(ps)
        session.commit()
        return ps

    @staticmethod
    def _create_service_request(session, client_id, service_id, address="Rua Destino, 100"):
        repo = ServiceRequestRepository(session=session)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address=address,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        return repo.create(sr)

    @staticmethod
    def _make_use_case_with_fake_sender(session, travel_price=Decimal("25.00")):
        fake_sender = FakeEmailSender()
        service_request_repository = ServiceRequestRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        travel_gateway = DeterministicTravelPriceGateway(fixed_price=travel_price)

        notification_service = NotifyServiceRequestConfirmationService(
            email_sender=fake_sender,
            user_repository=user_repository,
            service_repository=service_repository,
        )

        use_case = ConfirmServiceRequestUseCase(
            service_request_repository=service_request_repository,
            provider_service_repository=provider_service_repository,
            travel_price_gateway=travel_gateway,
            notification_service=notification_service,
        )

        return use_case, fake_sender

    def test_confirmation_dispatches_two_emails(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"}, name="Cliente Integração")
        provider = self._create_user(session, make_user, {"prestador"}, name="Prestador Integração")
        service = self._create_service(session, name="limpeza integração")

        self._create_provider_service(
            session=session,
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("100.00"),
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
        )

        use_case, fake_sender = self._make_use_case_with_fake_sender(
            session=session, travel_price=Decimal("25.00")
        )

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua Saida, 123",
        )

        output = use_case.execute(input_dto)

        assert output.status == ServiceRequestStatus.CONFIRMED.value
        assert len(fake_sender.client_confirmation_notifications_sent) == 1
        assert len(fake_sender.provider_confirmation_notifications_sent) == 1

    def test_notification_values_match_confirmed_prices(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        service_price = Decimal("150.00")
        travel_price = Decimal("30.00")

        client = self._create_user(session, make_user, {"cliente"}, name="Cliente Preço")
        provider = self._create_user(session, make_user, {"prestador"}, name="Prestador Preço")
        service = self._create_service(session, name="massagem integracao")

        self._create_provider_service(
            session=session,
            provider_id=provider.id,
            service_id=service.id,
            price=service_price,
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            address="Rua Destino, 999",
        )

        use_case, fake_sender = self._make_use_case_with_fake_sender(
            session=session, travel_price=travel_price
        )

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua Saida, 1",
        )

        use_case.execute(input_dto)

        client_notif = fake_sender.client_confirmation_notifications_sent[0]
        assert client_notif["service_price"] == service_price
        assert client_notif["travel_price"] == travel_price
        assert client_notif["total_price"] == service_price + travel_price
        assert client_notif["status"] == ServiceRequestStatus.CONFIRMED.value

        provider_notif = fake_sender.provider_confirmation_notifications_sent[0]
        assert provider_notif["service_price"] == service_price
        assert provider_notif["travel_price"] == travel_price
        assert provider_notif["total_price"] == service_price + travel_price
        assert provider_notif["service_address"] == "Rua Destino, 999"

    def test_request_stays_confirmed_if_notification_fails(self, tst_db_session, make_user, seed_roles):
        from unittest.mock import MagicMock

        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"}, name="Cliente Falha")
        provider = self._create_user(session, make_user, {"prestador"}, name="Prestador Falha")
        service = self._create_service(session, name="servico com falha")

        self._create_provider_service(
            session=session,
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("100.00"),
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
        )

        failing_notification_service = MagicMock()
        failing_notification_service.notify.side_effect = Exception("SMTP error")

        service_request_repository = ServiceRequestRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        travel_gateway = DeterministicTravelPriceGateway(fixed_price=Decimal("25.00"))

        use_case = ConfirmServiceRequestUseCase(
            service_request_repository=service_request_repository,
            provider_service_repository=provider_service_repository,
            travel_price_gateway=travel_gateway,
            notification_service=failing_notification_service,
        )

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua Saida, 1",
        )

        output = use_case.execute(input_dto)

        assert output.status == ServiceRequestStatus.CONFIRMED.value

        persisted = service_request_repository.find_by_id(service_request.id)
        assert persisted.status == ServiceRequestStatus.CONFIRMED.value