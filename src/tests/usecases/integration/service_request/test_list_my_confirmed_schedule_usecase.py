from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_dto import (
    ListMyConfirmedScheduleInputDTO,
)
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_usecase import (
    ListMyConfirmedScheduleUseCase,
)


class TestListMyConfirmedScheduleUseCase:
    @staticmethod
    def _create_provider(user_repository, make_user, *, name, email, is_active=True):
        provider = make_user(
            id=uuid4(),
            name=name,
            email=email,
            hashed_password="hashed_password",
            is_active=is_active,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        return provider

    @staticmethod
    def _create_client(user_repository, make_user, *, name, email):
        client = make_user(
            id=uuid4(),
            name=name,
            email=email,
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)
        return client

    @staticmethod
    def _create_service(service_repository, make_service, *, name, description=""):
        service = make_service(id=uuid4(), name=name, description=description)
        service_repository.create_service(service)
        return service

    @staticmethod
    def _create_confirmed_request(
        service_request_repository,
        *,
        client_id,
        service_id,
        provider_id,
        desired_datetime,
        address="Rua X, 123",
        service_price=Decimal("100.00"),
        travel_price=Decimal("25.00"),
        accepted_at=None,
    ):
        total_price = service_price + travel_price
        accepted_at = accepted_at or datetime(2026, 4, 5, 11, 30, 0)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=desired_datetime,
            address=address,
            status=ServiceRequestStatus.CONFIRMED.value,
            accepted_provider_id=provider_id,
            departure_address="Rua Partida, 1",
            service_price=service_price,
            travel_price=travel_price,
            total_price=total_price,
            accepted_at=accepted_at,
        )
        service_request_repository.create(sr)
        return sr

    def _make_use_case(self, session):
        sr_repo = ServiceRequestRepository(session=session)
        user_repo = userRepository(session=session)
        return ListMyConfirmedScheduleUseCase(
            service_request_repository=sr_repo,
            user_repository=user_repo,
        ), sr_repo

    def test_returns_only_confirmed_status(self, tst_db_session, make_user, make_service, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        svc_repo = ServiceRepository(session=session)
        sr_repo = ServiceRequestRepository(session=session)

        provider = self._create_provider(user_repo, make_user, name="Prestador", email="p1@example.com")
        client = self._create_client(user_repo, make_user, name="Cliente", email="c1@example.com")
        service = self._create_service(svc_repo, make_service, name="Instalação")

        self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 10, 10, 0, 0),
        )

        awaiting = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime(2026, 4, 11, 10, 0, 0),
            address="Rua Y, 1",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
        )
        sr_repo.create(awaiting)

        use_case, _ = self._make_use_case(session)
        output = use_case.execute(ListMyConfirmedScheduleInputDTO(provider_id=provider.id))

        assert len(output) == 1
        assert all(item.status == ServiceRequestStatus.CONFIRMED.value for item in output)

    def test_returns_only_logged_provider_requests(self, tst_db_session, make_user, make_service, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        svc_repo = ServiceRepository(session=session)
        sr_repo = ServiceRequestRepository(session=session)

        provider_a = self._create_provider(user_repo, make_user, name="Prestador A", email="pa@example.com")
        provider_b = self._create_provider(user_repo, make_user, name="Prestador B", email="pb@example.com")
        client = self._create_client(user_repo, make_user, name="Cliente", email="c2@example.com")
        service = self._create_service(svc_repo, make_service, name="Serviço X")

        req_a = self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider_a.id,
            desired_datetime=datetime(2026, 4, 10, 10, 0, 0),
        )
        self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider_b.id,
            desired_datetime=datetime(2026, 4, 11, 10, 0, 0),
        )

        use_case, _ = self._make_use_case(session)
        output = use_case.execute(ListMyConfirmedScheduleInputDTO(provider_id=provider_a.id))

        assert len(output) == 1
        assert str(output[0].service_request_id) == str(req_a.id)

    def test_respects_start_and_end_filter(self, tst_db_session, make_user, make_service, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        svc_repo = ServiceRepository(session=session)
        sr_repo = ServiceRequestRepository(session=session)

        provider = self._create_provider(user_repo, make_user, name="Prestador", email="p3@example.com")
        client = self._create_client(user_repo, make_user, name="Cliente", email="c3@example.com")
        service = self._create_service(svc_repo, make_service, name="Serviço Y")

        inside = self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 15, 10, 0, 0),
        )
        self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 3, 1, 10, 0, 0),
        )
        self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 5, 1, 10, 0, 0),
        )

        use_case, _ = self._make_use_case(session)
        output = use_case.execute(
            ListMyConfirmedScheduleInputDTO(
                provider_id=provider.id,
                start=datetime(2026, 4, 1, 0, 0, 0),
                end=datetime(2026, 4, 30, 23, 59, 59),
            )
        )

        assert len(output) == 1
        assert str(output[0].service_request_id) == str(inside.id)

    def test_without_filter_returns_all_confirmed(self, tst_db_session, make_user, make_service, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        svc_repo = ServiceRepository(session=session)
        sr_repo = ServiceRequestRepository(session=session)

        provider = self._create_provider(user_repo, make_user, name="Prestador", email="p4@example.com")
        client = self._create_client(user_repo, make_user, name="Cliente", email="c4@example.com")
        service = self._create_service(svc_repo, make_service, name="Serviço Z")

        for day in [10, 5, 20]:
            self._create_confirmed_request(
                sr_repo,
                client_id=client.id,
                service_id=service.id,
                provider_id=provider.id,
                desired_datetime=datetime(2026, 4, day, 10, 0, 0),
            )

        use_case, _ = self._make_use_case(session)
        output = use_case.execute(ListMyConfirmedScheduleInputDTO(provider_id=provider.id))

        assert len(output) == 3
        datetimes = [item.desired_datetime for item in output]
        assert datetimes == sorted(datetimes)

    def test_start_only_filter(self, tst_db_session, make_user, make_service, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        svc_repo = ServiceRepository(session=session)
        sr_repo = ServiceRequestRepository(session=session)

        provider = self._create_provider(user_repo, make_user, name="Prestador", email="p5@example.com")
        client = self._create_client(user_repo, make_user, name="Cliente", email="c5@example.com")
        service = self._create_service(svc_repo, make_service, name="Serviço W")

        after = self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 15, 10, 0, 0),
        )
        self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 3, 1, 10, 0, 0),
        )

        use_case, _ = self._make_use_case(session)
        output = use_case.execute(
            ListMyConfirmedScheduleInputDTO(
                provider_id=provider.id,
                start=datetime(2026, 4, 1, 0, 0, 0),
            )
        )

        assert len(output) == 1
        assert str(output[0].service_request_id) == str(after.id)

    def test_end_only_filter(self, tst_db_session, make_user, make_service, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        svc_repo = ServiceRepository(session=session)
        sr_repo = ServiceRequestRepository(session=session)

        provider = self._create_provider(user_repo, make_user, name="Prestador", email="p6@example.com")
        client = self._create_client(user_repo, make_user, name="Cliente", email="c6@example.com")
        service = self._create_service(svc_repo, make_service, name="Serviço V")

        before = self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 3, 1, 10, 0, 0),
        )
        self._create_confirmed_request(
            sr_repo,
            client_id=client.id,
            service_id=service.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 15, 10, 0, 0),
        )

        use_case, _ = self._make_use_case(session)
        output = use_case.execute(
            ListMyConfirmedScheduleInputDTO(
                provider_id=provider.id,
                end=datetime(2026, 3, 31, 23, 59, 59),
            )
        )

        assert len(output) == 1
        assert str(output[0].service_request_id) == str(before.id)

    def test_inactive_provider_raises_forbidden(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)

        provider = self._create_provider(
            user_repo, make_user, name="Inativo", email="inativo@example.com", is_active=False
        )

        use_case, _ = self._make_use_case(session)

        with pytest.raises(ForbiddenError):
            use_case.execute(ListMyConfirmedScheduleInputDTO(provider_id=provider.id))