"""
Testes de persistência — Fase 1: novos campos operacionais no ORM.

Cobre:
- Salva e lê os novos campos (IN_TRANSIT, ARRIVED, IN_PROGRESS)
- Registros antigos sem esses campos continuam funcionando com null
- Campos opcionais (travel_distance_km, logistics_reference) persistem corretamente
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


# ─── helpers ─────────────────────────────────────────────────────────────────


def _add_user(session, make_user, *, roles, **overrides):
    repo = userRepository(session=session)
    user = make_user(
        id=uuid4(),
        is_active=True,
        activation_code=None,
        activation_code_expires_at=None,
        roles=roles,
        **overrides
    )
    repo.add_user(user)
    session.commit()
    return user


def _add_service(session, make_service, name="Serviço Persist"):
    repo = ServiceRepository(session=session)
    svc = make_service(id=uuid4(), name=name)
    repo.create_service(svc)
    session.commit()
    return svc


def _make_base_confirmed(client_id, service_id, provider_id):
    now = datetime.utcnow()
    return ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Teste, 1",
        status=ServiceRequestStatus.CONFIRMED,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
    )


class TestServiceRequestOperationalFieldsPersistence:
    def test_confirmed_saves_and_reads_with_null_operational_fields(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """CONFIRMED sem campos de deslocamento: persistência mantém null nos novos campos."""
        cli = _add_user(
            tst_db_session, make_user, name="C1", email="c1_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P1",
            email="p1_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P1")

        repo = ServiceRequestRepository(session=tst_db_session)
        sr = _make_base_confirmed(cli.id, svc.id, prov.id)
        created = repo.create(sr)

        found = repo.find_by_id(created.id)
        assert found is not None
        assert found.travel_started_at is None
        assert found.route_calculated_at is None
        assert found.estimated_arrival_at is None
        assert found.travel_duration_minutes is None
        assert found.travel_distance_km is None
        assert found.provider_arrived_at is None
        assert found.client_confirmed_provider_arrival_at is None
        assert found.service_started_at is None
        assert found.logistics_reference is None

    def test_in_transit_fields_are_persisted_and_recovered(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Campos de deslocamento (IN_TRANSIT) são salvos e recuperados corretamente."""
        cli = _add_user(
            tst_db_session, make_user, name="C2", email="c2_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P2",
            email="p2_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P2")

        now = datetime.utcnow()
        travel_started = now + timedelta(minutes=5)
        route_calc = now + timedelta(minutes=5)
        estimated_arrival = now + timedelta(minutes=30)

        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Teste",
            status=ServiceRequestStatus.IN_TRANSIT,
            accepted_provider_id=prov.id,
            departure_address="Rua Origem",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            travel_started_at=travel_started,
            route_calculated_at=route_calc,
            estimated_arrival_at=estimated_arrival,
            travel_duration_minutes=25,
            travel_distance_km=Decimal("8.50"),
            logistics_reference="ref-123",
        )

        repo = ServiceRequestRepository(session=tst_db_session)
        created = repo.create(sr)
        found = repo.find_by_id(created.id)

        assert found is not None
        assert found.status == ServiceRequestStatus.IN_TRANSIT.value
        assert found.travel_duration_minutes == 25
        assert found.travel_distance_km == Decimal("8.50")
        assert found.logistics_reference == "ref-123"
        assert found.provider_arrived_at is None
        assert found.service_started_at is None
        # Compara apenas até segundos para evitar problemas de arredondamento de microsegundos no SQLite
        assert abs((found.travel_started_at - travel_started).total_seconds()) < 1
        assert abs((found.estimated_arrival_at - estimated_arrival).total_seconds()) < 1

    def test_arrived_fields_are_persisted(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Campo provider_arrived_at (ARRIVED) é salvo e recuperado."""
        cli = _add_user(
            tst_db_session, make_user, name="C3", email="c3_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P3",
            email="p3_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P3")

        now = datetime.utcnow()
        arrived_at = now + timedelta(minutes=28)

        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Teste",
            status=ServiceRequestStatus.ARRIVED,
            accepted_provider_id=prov.id,
            departure_address="Rua Origem",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            travel_started_at=now + timedelta(minutes=5),
            route_calculated_at=now + timedelta(minutes=5),
            estimated_arrival_at=now + timedelta(minutes=30),
            travel_duration_minutes=25,
            provider_arrived_at=arrived_at,
        )

        repo = ServiceRequestRepository(session=tst_db_session)
        created = repo.create(sr)
        found = repo.find_by_id(created.id)

        assert found is not None
        assert found.status == ServiceRequestStatus.ARRIVED.value
        assert abs((found.provider_arrived_at - arrived_at).total_seconds()) < 1
        assert found.service_started_at is None

    def test_in_progress_fields_are_persisted(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """Campos de início de serviço (IN_PROGRESS) são salvos e recuperados."""
        cli = _add_user(
            tst_db_session, make_user, name="C4", email="c4_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P4",
            email="p4_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P4")

        now = datetime.utcnow()
        confirmed_at = now + timedelta(minutes=32)
        started_at = now + timedelta(minutes=32)

        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Teste",
            status=ServiceRequestStatus.IN_PROGRESS,
            accepted_provider_id=prov.id,
            departure_address="Rua Origem",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            travel_started_at=now + timedelta(minutes=5),
            route_calculated_at=now + timedelta(minutes=5),
            estimated_arrival_at=now + timedelta(minutes=30),
            travel_duration_minutes=25,
            provider_arrived_at=now + timedelta(minutes=28),
            client_confirmed_provider_arrival_at=confirmed_at,
            service_started_at=started_at,
        )

        repo = ServiceRequestRepository(session=tst_db_session)
        created = repo.create(sr)
        found = repo.find_by_id(created.id)

        assert found is not None
        assert found.status == ServiceRequestStatus.IN_PROGRESS.value
        assert abs((found.service_started_at - started_at).total_seconds()) < 1
        assert (
            abs(
                (
                    found.client_confirmed_provider_arrival_at - confirmed_at
                ).total_seconds()
            )
            < 1
        )

    def test_update_propagates_operational_fields(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """update() persiste corretamente campos do ciclo operacional."""
        cli = _add_user(
            tst_db_session, make_user, name="C5", email="c5_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P5",
            email="p5_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P5")

        repo = ServiceRequestRepository(session=tst_db_session)
        sr = _make_base_confirmed(cli.id, svc.id, prov.id)
        created = repo.create(sr)

        # Simula transição para IN_TRANSIT via update
        now = datetime.utcnow()
        created.status = ServiceRequestStatus.IN_TRANSIT.value
        created.travel_started_at = now + timedelta(minutes=5)
        created.route_calculated_at = now + timedelta(minutes=5)
        created.estimated_arrival_at = now + timedelta(minutes=30)
        created.travel_duration_minutes = 25
        created.logistics_reference = "ref-update"

        updated = repo.update(created)
        assert updated.status == ServiceRequestStatus.IN_TRANSIT.value
        assert updated.travel_duration_minutes == 25
        assert updated.logistics_reference == "ref-update"

    def test_list_confirmed_schedule_includes_in_transit(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """list_operational_schedule_for_provider lista IN_TRANSIT (Caminho B)."""
        cli = _add_user(
            tst_db_session, make_user, name="C6", email="c6_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P6",
            email="p6_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P6")

        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Teste",
            status=ServiceRequestStatus.IN_TRANSIT,
            accepted_provider_id=prov.id,
            departure_address="Rua Origem",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=now,
            travel_started_at=now + timedelta(minutes=5),
            route_calculated_at=now + timedelta(minutes=5),
            estimated_arrival_at=now + timedelta(minutes=30),
            travel_duration_minutes=25,
        )

        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        items = repo.list_operational_schedule_for_provider(provider_id=prov.id)
        assert len(items) == 1
        assert items[0].status == ServiceRequestStatus.IN_TRANSIT.value
        assert items[0].travel_duration_minutes == 25

    def test_list_confirmed_schedule_includes_all_operational_statuses(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        """list_operational_schedule_for_provider lista todos os 4 status operacionais."""
        cli = _add_user(
            tst_db_session, make_user, name="C7", email="c7_p@e.com", roles={"cliente"}
        )
        prov = _add_user(
            tst_db_session,
            make_user,
            name="P7",
            email="p7_p@e.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service, "Serviço P7")

        now = datetime.utcnow()
        confirmed = _make_base_confirmed(cli.id, svc.id, prov.id)

        def _make_in_transit():
            return ServiceRequest(
                id=uuid4(),
                client_id=cli.id,
                service_id=svc.id,
                desired_datetime=now + timedelta(days=2),
                address="Rua",
                status=ServiceRequestStatus.IN_TRANSIT,
                accepted_provider_id=prov.id,
                departure_address="Orig",
                service_price=Decimal("100"),
                travel_price=Decimal("20"),
                total_price=Decimal("120"),
                accepted_at=now,
                travel_started_at=now + timedelta(minutes=5),
                route_calculated_at=now + timedelta(minutes=5),
                estimated_arrival_at=now + timedelta(minutes=30),
                travel_duration_minutes=25,
            )

        def _make_arrived():
            return ServiceRequest(
                id=uuid4(),
                client_id=cli.id,
                service_id=svc.id,
                desired_datetime=now + timedelta(days=3),
                address="Rua",
                status=ServiceRequestStatus.ARRIVED,
                accepted_provider_id=prov.id,
                departure_address="Orig",
                service_price=Decimal("100"),
                travel_price=Decimal("20"),
                total_price=Decimal("120"),
                accepted_at=now,
                travel_started_at=now + timedelta(minutes=5),
                route_calculated_at=now + timedelta(minutes=5),
                estimated_arrival_at=now + timedelta(minutes=30),
                travel_duration_minutes=25,
                provider_arrived_at=now + timedelta(minutes=28),
            )

        def _make_in_progress():
            return ServiceRequest(
                id=uuid4(),
                client_id=cli.id,
                service_id=svc.id,
                desired_datetime=now + timedelta(days=4),
                address="Rua",
                status=ServiceRequestStatus.IN_PROGRESS,
                accepted_provider_id=prov.id,
                departure_address="Orig",
                service_price=Decimal("100"),
                travel_price=Decimal("20"),
                total_price=Decimal("120"),
                accepted_at=now,
                travel_started_at=now + timedelta(minutes=5),
                route_calculated_at=now + timedelta(minutes=5),
                estimated_arrival_at=now + timedelta(minutes=30),
                travel_duration_minutes=25,
                provider_arrived_at=now + timedelta(minutes=28),
                client_confirmed_provider_arrival_at=now + timedelta(minutes=32),
                service_started_at=now + timedelta(minutes=32),
            )

        repo = ServiceRequestRepository(session=tst_db_session)
        for sr in [confirmed, _make_in_transit(), _make_arrived(), _make_in_progress()]:
            repo.create(sr)
        tst_db_session.commit()

        items = repo.list_operational_schedule_for_provider(provider_id=prov.id)
        assert len(items) == 4
        statuses = {item.status for item in items}
        assert statuses == {"CONFIRMED", "IN_TRANSIT", "ARRIVED", "IN_PROGRESS"}
