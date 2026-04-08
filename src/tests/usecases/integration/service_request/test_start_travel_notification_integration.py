from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)

from domain.notification.notification_exceptions import EmailDeliveryError
import pytest

from domain.logistics.logistics_acl_gateway_interface import LogisticsAclGatewayInterface
from domain.logistics.route_estimate_dto import RouteEstimateDTO
from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.fakes.fake_email_sender import FakeEmailSender
from usecases.service_request.start_provider_travel.start_provider_travel_dto import (
    StartProviderTravelInputDTO,
)
from usecases.service_request.start_provider_travel.start_provider_travel_usecase import (
    StartProviderTravelUseCase,
)


class DeterministicLogisticsGateway(LogisticsAclGatewayInterface):
    def __init__(self, duration_minutes: int = 25, distance_km: Decimal = Decimal("8.5")):
        self._duration_minutes = duration_minutes
        self._distance_km = distance_km

    def estimate_route(
        self,
        origin_address: str,
        destination_address: str,
        departure_at: datetime,
    ) -> RouteEstimateDTO:
        return RouteEstimateDTO(
            duration_minutes=self._duration_minutes,
            distance_km=self._distance_km,
            estimated_arrival_at=departure_at + timedelta(minutes=self._duration_minutes),
            reference="test-ref",
        )


class TestStartTravelEmailNotificationIntegration:
    @staticmethod
    def _create_user(session, make_user, roles, name=None, email=None):
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
    def _create_confirmed_sr(session, client_id, provider_id):
        from infrastructure.service.sqlalchemy.service_model import ServiceModel

        service = ServiceModel(id=uuid4(), name=f"Srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Destino, 100",
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=provider_id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
        )
        repo = ServiceRequestRepository(session=session)
        result = repo.create(sr)
        session.commit()
        return result

    @staticmethod
    def _make_use_case_with_fake_sender(session, duration_minutes=25):
        fake_sender = FakeEmailSender()
        service_request_repository = ServiceRequestRepository(session=session)
        user_repo = userRepository(session=session)
        notification_gateway = EmailServiceRequestNotificationGateway(
            email_sender=fake_sender,
            user_repository=user_repo,
        )
        logistics_gateway = DeterministicLogisticsGateway(duration_minutes=duration_minutes)

        use_case = StartProviderTravelUseCase(
            service_request_repository=service_request_repository,
            logistics_acl_gateway=logistics_gateway,
            notification_gateway=notification_gateway,
        )
        return use_case, fake_sender

    def test_dispatches_travel_started_email_to_client(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_user(
            session, make_user, {"cliente"}, name="Cliente Viagem", email=f"cli_{uuid4().hex}@example.com"
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, name="Prestador Viagem", email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_confirmed_sr(session, client.id, provider.id)

        use_case, fake_sender = self._make_use_case_with_fake_sender(session)

        use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider.id,
                service_request_id=sr.id,
            )
        )

        assert len(fake_sender.travel_started_notifications_sent) == 1

    def test_email_contains_correct_client_data(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_email = f"cli_{uuid4().hex}@example.com"
        client_name = "Maria Cliente"
        client = self._create_user(
            session, make_user, {"cliente"}, name=client_name, email=client_email
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_confirmed_sr(session, client.id, provider.id)

        use_case, fake_sender = self._make_use_case_with_fake_sender(session, duration_minutes=30)

        use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider.id,
                service_request_id=sr.id,
            )
        )

        notif = fake_sender.travel_started_notifications_sent[0]
        assert notif["client_email"] == client_email
        assert notif["client_name"] == client_name
        assert notif["travel_duration_minutes"] == 30
        assert notif["estimated_arrival_at"] is not None

    def test_notification_failure_does_not_revert_in_transit(self, tst_db_session, make_user, seed_roles):

        session = tst_db_session
        client = self._create_user(
            session, make_user, {"cliente"}, email=f"cli_{uuid4().hex}@example.com"
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_confirmed_sr(session, client.id, provider.id)

        failing_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        failing_gateway.notify_client_travel_started.side_effect = EmailDeliveryError("SMTP error")

        use_case = StartProviderTravelUseCase(
            service_request_repository=ServiceRequestRepository(session=session),
            logistics_acl_gateway=DeterministicLogisticsGateway(),
            notification_gateway=failing_gateway,
        )

        output = use_case.execute(
            StartProviderTravelInputDTO(
                authenticated_user_id=provider.id,
                service_request_id=sr.id,
            )
        )

        assert output.status == ServiceRequestStatus.IN_TRANSIT.value

        persisted = ServiceRequestRepository(session=session).find_by_id(sr.id)
        assert persisted.status == ServiceRequestStatus.IN_TRANSIT.value



    def test_logistics_failure_does_not_persist_in_transit(
        self, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session

        client = self._create_user(
            session, make_user, {"cliente"}, email=f"cli_{uuid4().hex}@example.com"
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_confirmed_sr(session, client.id, provider.id)

        class FailingLogisticsGateway(LogisticsAclGatewayInterface):
            def estimate_route(
                self,
                origin_address: str,
                destination_address: str,
                departure_at: datetime,
            ) -> RouteEstimateDTO:
                raise RuntimeError("ACL down")

        use_case = StartProviderTravelUseCase(
            service_request_repository=ServiceRequestRepository(session=session),
            logistics_acl_gateway=FailingLogisticsGateway(),
            notification_gateway=None,
        )

        with pytest.raises(RuntimeError, match="ACL down"):
            use_case.execute(
                StartProviderTravelInputDTO(
                    authenticated_user_id=provider.id,
                    service_request_id=sr.id,
                )
            )

        persisted = ServiceRequestRepository(session=session).find_by_id(sr.id)
        assert persisted.status == ServiceRequestStatus.CONFIRMED.value
        assert persisted.travel_started_at is None
        assert persisted.route_calculated_at is None
        assert persisted.estimated_arrival_at is None

