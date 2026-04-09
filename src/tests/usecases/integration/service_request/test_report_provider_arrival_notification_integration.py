from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)
import pytest

from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from infrastructure.notification.email_notification_gateway import (
    EmailServiceRequestNotificationGateway,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.fakes.fake_email_sender import FakeEmailSender
from usecases.service_request.report_provider_arrival.report_provider_arrival_dto import (
    ReportProviderArrivalInputDTO,
)
from usecases.service_request.report_provider_arrival.report_provider_arrival_usecase import (
    ReportProviderArrivalUseCase,
)


class TestReportProviderArrivalNotificationIntegration:
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
    def _create_in_transit_sr(session, client_id, provider_id):
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
            status=ServiceRequestStatus.IN_TRANSIT,
            accepted_provider_id=provider_id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now - timedelta(hours=1),
            travel_started_at=now - timedelta(minutes=15),
            route_calculated_at=now - timedelta(minutes=15),
            estimated_arrival_at=now + timedelta(minutes=10),
            travel_duration_minutes=25,
        )
        repo = ServiceRequestRepository(session=session)
        result = repo.create(sr)
        session.commit()
        return result

    @staticmethod
    def _make_use_case_with_fake_sender(session):
        fake_sender = FakeEmailSender()
        service_request_repository = ServiceRequestRepository(session=session)
        user_repo = userRepository(session=session)
        notification_gateway = EmailServiceRequestNotificationGateway(
            email_sender=fake_sender,
            user_repository=user_repo,
        )

        use_case = ReportProviderArrivalUseCase(
            service_request_repository=service_request_repository,
            notification_gateway=notification_gateway,
        )
        return use_case, fake_sender

    def test_dispatches_arrived_email_to_client(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_user(
            session, make_user, {"cliente"},
            name="Cliente Chegada", email=f"cli_{uuid4().hex}@example.com"
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_in_transit_sr(session, client.id, provider.id)

        use_case, fake_sender = self._make_use_case_with_fake_sender(session)

        use_case.execute(
            ReportProviderArrivalInputDTO(
                authenticated_user_id=provider.id,
                service_request_id=sr.id,
            )
        )

        assert len(fake_sender.provider_arrived_notifications_sent) == 1

    def test_email_contains_correct_client_and_time(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_email = f"cli_{uuid4().hex}@example.com"
        client_name = "Maria Chegada"
        client = self._create_user(
            session, make_user, {"cliente"}, name=client_name, email=client_email
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_in_transit_sr(session, client.id, provider.id)

        use_case, fake_sender = self._make_use_case_with_fake_sender(session)

        use_case.execute(
            ReportProviderArrivalInputDTO(
                authenticated_user_id=provider.id,
                service_request_id=sr.id,
            )
        )

        notif = fake_sender.provider_arrived_notifications_sent[0]
        assert notif["client_email"] == client_email
        assert notif["client_name"] == client_name
        assert notif["provider_arrived_at"] is not None

    def test_notification_failure_does_not_revert_arrived(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client = self._create_user(
            session, make_user, {"cliente"}, email=f"cli_{uuid4().hex}@example.com"
        )
        provider = self._create_user(
            session, make_user, {"prestador"}, email=f"prov_{uuid4().hex}@example.com"
        )
        sr = self._create_in_transit_sr(session, client.id, provider.id)

        failing_gateway = MagicMock(spec=ServiceRequestNotificationGatewayInterface)
        failing_gateway.notify_client_provider_arrived.side_effect = EmailDeliveryError("SMTP error")

        use_case = ReportProviderArrivalUseCase(
            service_request_repository=ServiceRequestRepository(session=session),
            notification_gateway=failing_gateway,
        )

        output = use_case.execute(
            ReportProviderArrivalInputDTO(
                authenticated_user_id=provider.id,
                service_request_id=sr.id,
            )
        )

        assert output.status == ServiceRequestStatus.ARRIVED.value

        persisted = ServiceRequestRepository(session=session).find_by_id(sr.id)
        assert persisted.status == ServiceRequestStatus.ARRIVED.value
        assert persisted.provider_arrived_at is not None