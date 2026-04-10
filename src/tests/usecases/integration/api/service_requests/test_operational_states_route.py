
"""
Testes de integração — Fase 1: novos campos operacionais nos endpoints de leitura.

Cobre:
- GET /user-service-requests/me retorna os novos campos (travel_started_at, etc.)
- Registros antigos sem esses campos continuam retornando null
- GET /provider-schedule/me retorna os novos campos
- GET /provider-schedule/me lista status operacionais (IN_TRANSIT, ARRIVED, IN_PROGRESS)
"""
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_auth_header(user):
    token_service = make_token_service()
    roles = [r.name if hasattr(r, "name") else str(r) for r in user.roles]
    data = CreateAccessTokenDTO(sub=str(user.id), email=user.email, roles=sorted(roles))
    return {"Authorization": f"Bearer {token_service.create_access_token(data=data)}"}


def _add_user(session, make_user, *, roles, **overrides):
    repo = userRepository(session=session)
    user = make_user(
        id=uuid4(),
        is_active=True,
        activation_code=None,
        activation_code_expires_at=None,
        roles=roles,
        **overrides,
    )
    repo.add_user(user)
    session.commit()
    return user


def _add_service(session, make_service, name="Serviço Teste"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _base_confirmed_request(client_id, service_id, provider_id, desired_datetime=None):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=desired_datetime or (now + timedelta(days=1)),
        address="Rua Teste, 123",
        status=ServiceRequestStatus.CONFIRMED,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
    )


def _base_in_transit_request(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 123",
        status=ServiceRequestStatus.IN_TRANSIT,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        travel_started_at=now + timedelta(minutes=5),
        route_calculated_at=now + timedelta(minutes=5),
        estimated_arrival_at=now + timedelta(minutes=30),
        travel_duration_minutes=25,
        travel_distance_km=Decimal("8.5"),
        logistics_reference="mock-logistics-ref",
    )


def _base_arrived_request(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 123",
        status=ServiceRequestStatus.ARRIVED,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        travel_started_at=now + timedelta(minutes=5),
        route_calculated_at=now + timedelta(minutes=5),
        estimated_arrival_at=now + timedelta(minutes=30),
        travel_duration_minutes=25,
        provider_arrived_at=now + timedelta(minutes=28),
    )


def _base_in_progress_request(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 123",
        status=ServiceRequestStatus.IN_PROGRESS,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        travel_started_at=now + timedelta(minutes=5),
        route_calculated_at=now + timedelta(minutes=5),
        estimated_arrival_at=now + timedelta(minutes=30),
        travel_duration_minutes=25,
        provider_arrived_at=now + timedelta(minutes=28),
        client_confirmed_provider_arrival_at=now + timedelta(minutes=32),
        service_started_at=now + timedelta(minutes=32),
    )


# ─── Testes do cliente ────────────────────────────────────────────────────────

class TestListMyServiceRequestsOperationalFields:
    def test_old_records_return_null_for_new_fields(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Registros antigos (CONFIRMED sem campos de deslocamento) retornam null nos campos novos."""
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_old@example.com", roles={"cliente"}
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_old@example.com", roles={"prestador"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Antigo")

        sr = _base_confirmed_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/user-service-requests/me", headers=_make_auth_header(cli))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["travel_started_at"] is None
        assert item["estimated_arrival_at"] is None
        assert item["travel_duration_minutes"] is None
        assert item["travel_distance_km"] is None
        assert item["provider_arrived_at"] is None
        assert item["service_started_at"] is None
        assert item["service_finished_at"] is None
        assert item["payment_requested_at"] is None
        assert item["payment_processing_started_at"] is None
        assert item["payment_approved_at"] is None
        assert item["payment_refused_at"] is None
        assert item["service_concluded_at"] is None
        assert item["payment_last_status"] is None
        assert item["payment_amount"] is None



    def test_in_transit_fields_are_serialized(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Um ServiceRequest IN_TRANSIT expõe travel_started_at, estimated_arrival_at e travel_duration_minutes."""
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_transit@example.com", roles={"cliente"}
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_transit@example.com", roles={"prestador"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Transit")

        sr = _base_in_transit_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/user-service-requests/me", headers=_make_auth_header(cli))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["status"] == "IN_TRANSIT"
        assert item["travel_started_at"] is not None
        assert item["estimated_arrival_at"] is not None
        assert item["travel_duration_minutes"] == 25
        assert Decimal(str(item["travel_distance_km"])) == Decimal("8.5")
        assert item["provider_arrived_at"] is None
        assert item["service_started_at"] is None

    def test_in_progress_fields_are_serialized(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Um ServiceRequest IN_PROGRESS expõe service_started_at e provider_arrived_at."""
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_prog@example.com", roles={"cliente"}
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_prog@example.com", roles={"prestador"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Progresso")

        sr = _base_in_progress_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/user-service-requests/me", headers=_make_auth_header(cli))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["status"] == "IN_PROGRESS"
        assert item["travel_started_at"] is not None
        assert item["provider_arrived_at"] is not None
        assert item["service_started_at"] is not None


# ─── Testes da agenda do prestador ───────────────────────────────────────────

class TestProviderScheduleOperationalFields:
    def test_provider_schedule_returns_null_fields_for_confirmed(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """CONFIRMED sem campos de deslocamento retorna null nos campos novos da agenda."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_sched_null@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_sched_null@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Schedule Null")

        sr = _base_confirmed_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["travel_started_at"] is None
        assert item["estimated_arrival_at"] is None
        assert item["travel_duration_minutes"] is None
        assert item["provider_arrived_at"] is None
        assert item["service_started_at"] is None
        assert item["service_finished_at"] is None
        assert item["payment_requested_at"] is None
        assert item["payment_last_status"] is None
        assert item["service_concluded_at"] is None
        

    def test_provider_schedule_lists_in_transit_status(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Agenda do prestador inclui status IN_TRANSIT (Caminho B)."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_in_transit@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_in_transit@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço InTransit")

        sr = _base_in_transit_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["status"] == "IN_TRANSIT"
        assert item["travel_started_at"] is not None
        assert item["estimated_arrival_at"] is not None
        assert item["travel_duration_minutes"] == 25

    def test_provider_schedule_lists_arrived_status(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Agenda do prestador inclui status ARRIVED."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_arrived@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_arrived@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Arrived")

        sr = _base_arrived_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["status"] == "ARRIVED"
        assert item["provider_arrived_at"] is not None

    def test_provider_schedule_lists_in_progress_status(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Agenda do prestador inclui status IN_PROGRESS."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_in_progress@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_in_progress@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço InProgress")

        sr = _base_in_progress_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        item = body[0]
        assert item["status"] == "IN_PROGRESS"
        assert item["service_started_at"] is not None

    def test_provider_schedule_lists_all_operational_statuses(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Agenda do prestador lista CONFIRMED + IN_TRANSIT + ARRIVED + IN_PROGRESS juntos."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_all_ops@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_all_ops@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço All Ops")

        repo = ServiceRequestRepository(session=tst_db_session)
        confirmed = _base_confirmed_request(cli.id, svc.id, provider.id, datetime.utcnow() + timedelta(days=4))
        in_transit = _base_in_transit_request(cli.id, svc.id, provider.id)
        arrived = _base_arrived_request(cli.id, svc.id, provider.id)
        in_progress = _base_in_progress_request(cli.id, svc.id, provider.id)

        for sr in [confirmed, in_transit, arrived, in_progress]:
            repo.create(sr)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 4
        statuses = {item["status"] for item in body}
        assert statuses == {"CONFIRMED", "IN_TRANSIT", "ARRIVED", "IN_PROGRESS"}

    def test_provider_schedule_excludes_non_operational_statuses(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Agenda do prestador não lista AWAITING_PROVIDER_ACCEPTANCE, DECLINED, etc."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_excl@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_excl@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Excluido")

        repo = ServiceRequestRepository(session=tst_db_session)
        awaiting = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua X",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE,
        )
        repo.create(awaiting)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        assert response.json() == []

    def test_in_transit_fields_in_provider_schedule_response(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Verifica que os campos operacionais novos estão presentes na resposta da agenda."""
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email="prov_fields_check@example.com", roles={"prestador"}
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email="cli_fields_check@example.com", roles={"cliente"}
        )
        svc = _add_service(tst_db_session, make_service, "Serviço Fields")

        sr = _base_in_transit_request(cli.id, svc.id, provider.id)
        ServiceRequestRepository(session=tst_db_session).create(sr)
        tst_db_session.commit()

        response = client.get("/provider-schedule/me", headers=_make_auth_header(provider))
        assert response.status_code == 200
        item = response.json()[0]

        # verifica campos novos presentes
        assert "travel_started_at" in item
        assert "estimated_arrival_at" in item
        assert "travel_duration_minutes" in item
        assert "provider_arrived_at" in item
        assert "service_started_at" in item
