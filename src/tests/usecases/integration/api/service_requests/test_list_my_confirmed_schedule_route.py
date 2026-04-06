from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import ServiceRequest, ServiceRequestStatus
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestListMyConfirmedScheduleRoute:
    def _make_auth_header(self, user):
        token_service = make_token_service()
        roles = []
        for role in user.roles:
            if hasattr(role, "name"):
                roles.append(role.name)
            else:
                roles.append(str(role))
        data = CreateAccessTokenDTO(
            sub=str(user.id),
            email=user.email,
            roles=sorted(roles),
        )
        access_token = token_service.create_access_token(data=data)
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _create_provider(session, make_user, *, name, email, is_active=True):
        repo = userRepository(session=session)
        user = make_user(
            id=uuid4(),
            name=name,
            email=email,
            hashed_password="hashed_password",
            is_active=is_active,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        repo.add_user(user)
        session.commit()
        return user

    @staticmethod
    def _create_client(session, make_user, *, name, email):
        repo = userRepository(session=session)
        user = make_user(
            id=uuid4(),
            name=name,
            email=email,
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        repo.add_user(user)
        session.commit()
        return user

    @staticmethod
    def _create_service(session, make_service, *, name, description=""):
        repo = ServiceRepository(session=session)
        service = make_service(id=uuid4(), name=name, description=description)
        repo.create_service(service)
        session.commit()
        return service

    @staticmethod
    def _create_confirmed_request(
        session,
        *,
        client_id,
        service_id,
        provider_id,
        desired_datetime,
        address="Rua X, 123",
        service_price=Decimal("100.00"),
        travel_price=Decimal("25.00"),
    ):
        repo = ServiceRequestRepository(session=session)
        total_price = service_price + travel_price
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
            accepted_at=datetime(2026, 4, 5, 11, 30, 0),
        )
        repo.create(sr)
        session.commit()
        return sr

    def test_requires_authentication(self, client):
        response = client.get("/provider-schedule/me")
        assert response.status_code == 401

    def test_forbidden_for_client_role(self, client, tst_db_session, make_user, seed_roles):
        user = self._create_client(tst_db_session, make_user, name="Cliente", email="cli@example.com")
        headers = self._make_auth_header(user)
        response = client.get("/provider-schedule/me", headers=headers)
        assert response.status_code == 403

    def test_returns_only_confirmed_items(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_conf@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_conf@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Serviço Confirmado")

        confirmed = self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 10, 10, 0, 0),
        )

        awaiting = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=datetime(2026, 4, 11, 10, 0, 0),
            address="Rua Y, 1",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
        )
        ServiceRequestRepository(session=tst_db_session).create(awaiting)
        tst_db_session.commit()

        headers = self._make_auth_header(provider)
        response = client.get("/provider-schedule/me", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(confirmed.id)
        assert body[0]["status"] == "CONFIRMED"

    def test_returns_only_logged_provider_requests(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider_a = self._create_provider(tst_db_session, make_user, name="Prestador A", email="pa_route@example.com")
        provider_b = self._create_provider(tst_db_session, make_user, name="Prestador B", email="pb_route@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_route@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Serviço Route")

        req_a = self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider_a.id,
            desired_datetime=datetime(2026, 4, 10, 10, 0, 0),
        )
        self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider_b.id,
            desired_datetime=datetime(2026, 4, 11, 10, 0, 0),
        )

        headers = self._make_auth_header(provider_a)
        response = client.get("/provider-schedule/me", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(req_a.id)

    def test_respects_start_and_end_filter(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_period@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_period@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Serviço Period")

        inside = self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 15, 10, 0, 0),
        )
        self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 3, 1, 10, 0, 0),
        )
        self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 5, 1, 10, 0, 0),
        )

        headers = self._make_auth_header(provider)
        response = client.get(
            "/provider-schedule/me",
            params={"start": "2026-04-01T00:00:00", "end": "2026-04-30T23:59:59"},
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(inside.id)

    def test_without_filter_returns_all_confirmed_ordered(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_all@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_all@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Serviço All")

        for day in [20, 5, 10]:
            self._create_confirmed_request(
                tst_db_session,
                client_id=cli.id,
                service_id=svc.id,
                provider_id=provider.id,
                desired_datetime=datetime(2026, 4, day, 10, 0, 0),
            )

        headers = self._make_auth_header(provider)
        response = client.get("/provider-schedule/me", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 3
        datetimes = [item["desired_datetime"] for item in body]
        assert datetimes == sorted(datetimes)

    def test_start_only_filter(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_start@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_start@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Serviço Start")

        after = self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 15, 10, 0, 0),
        )
        self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 3, 1, 10, 0, 0),
        )

        headers = self._make_auth_header(provider)
        response = client.get(
            "/provider-schedule/me",
            params={"start": "2026-04-01T00:00:00"},
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(after.id)

    def test_end_only_filter(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_end@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_end@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Serviço End")

        before = self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 3, 1, 10, 0, 0),
        )
        self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 15, 10, 0, 0),
        )

        headers = self._make_auth_header(provider)
        response = client.get(
            "/provider-schedule/me",
            params={"end": "2026-03-31T23:59:59"},
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(before.id)

    def test_invalid_period_returns_422(self, client, tst_db_session, make_user, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_422@example.com")
        headers = self._make_auth_header(provider)

        response = client.get(
            "/provider-schedule/me",
            params={"start": "2026-04-30T00:00:00", "end": "2026-04-01T00:00:00"},
            headers=headers,
        )

        assert response.status_code == 422

    def test_empty_schedule_returns_empty_list(self, client, tst_db_session, make_user, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_empty@example.com")
        headers = self._make_auth_header(provider)

        response = client.get("/provider-schedule/me", headers=headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_response_contains_expected_fields(self, client, tst_db_session, make_user, make_service, seed_roles):
        provider = self._create_provider(tst_db_session, make_user, name="Prestador", email="p_fields@example.com")
        cli = self._create_client(tst_db_session, make_user, name="Cliente", email="c_fields@example.com")
        svc = self._create_service(tst_db_session, make_service, name="Instalação", description="Instalação técnica")

        self._create_confirmed_request(
            tst_db_session,
            client_id=cli.id,
            service_id=svc.id,
            provider_id=provider.id,
            desired_datetime=datetime(2026, 4, 10, 10, 0, 0),
            address="Rua Teste, 99",
            service_price=Decimal("100.00"),
            travel_price=Decimal("25.00"),
        )

        headers = self._make_auth_header(provider)
        response = client.get("/provider-schedule/me", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]

        assert "service_request_id" in item
        assert "service_id" in item
        assert "service_name" in item
        assert "service_description" in item
        assert "client_id" in item
        assert "desired_datetime" in item
        assert "address" in item
        assert "status" in item
        assert "service_price" in item
        assert "travel_price" in item
        assert "total_price" in item
        assert "accepted_at" in item

        assert item["status"] == "CONFIRMED"
        assert item["service_name"] == "Instalação"
        assert item["address"] == "Rua Teste, 99"
        assert item["client_id"] == str(cli.id)