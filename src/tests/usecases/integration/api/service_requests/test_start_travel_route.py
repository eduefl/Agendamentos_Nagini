from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


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


def _add_service(session, make_service, name=None):
    svc = make_service(id=uuid4(), name=name or f"Srv {uuid4().hex}")
    from infrastructure.service.sqlalchemy.service_repository import ServiceRepository

    ServiceRepository(session=session).create_service(svc)
    session.commit()
    return svc


def _create_confirmed_sr(
    session, client_id, service_id, provider_id, expires_delta=None
):
    now = datetime.utcnow()
    sr = ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Destino, 100",
        status=ServiceRequestStatus.CONFIRMED,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now,
        expires_at=(now + expires_delta) if expires_delta is not None else None,
    )
    repo = ServiceRequestRepository(session=session)
    result = repo.create(sr)
    session.commit()
    return result


class TestStartTravelRoute:
    def test_requires_auth(self, client):
        response = client.patch(f"/provider-schedule/{uuid4()}/start-travel")
        assert response.status_code == 401

    def test_rejects_client_role(self, client, tst_db_session, make_user, seed_roles):
        client_user = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        response = client.patch(
            f"/provider-schedule/{uuid4()}/start-travel",
            headers=_make_auth_header(client_user),
        )
        assert response.status_code == 403

    def test_returns_404_when_not_found(
        self, client, tst_db_session, make_user, seed_roles
    ):
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        response = client.patch(
            f"/provider-schedule/{uuid4()}/start-travel",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 404

    def test_returns_403_when_provider_not_owner(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador Dono",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        other_provider = _add_user(
            tst_db_session,
            make_user,
            name="Outro Prestador",
            email=f"prov2_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)

        # other_provider tries to start travel
        response = client.patch(
            f"/provider-schedule/{sr.id}/start-travel",
            headers=_make_auth_header(other_provider),
        )
        assert response.status_code == 403

    def test_returns_409_when_status_not_confirmed(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)

        # Force status to IN_TRANSIT via raw model update
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update(
            {
                "status": ServiceRequestStatus.IN_TRANSIT.value,
                "travel_started_at": datetime.utcnow(),
                "route_calculated_at": datetime.utcnow(),
                "estimated_arrival_at": datetime.utcnow() + timedelta(minutes=25),
                "travel_duration_minutes": 25,
            }
        )
        tst_db_session.commit()

        response = client.patch(
            f"/provider-schedule/{sr.id}/start-travel",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 409

    def test_returns_409_when_expired(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(
            tst_db_session,
            cli.id,
            svc.id,
            provider.id,
            expires_delta=timedelta(hours=1),
        )

        # Force expires_at into the past
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update({"expires_at": datetime.utcnow() - timedelta(minutes=5)})
        tst_db_session.commit()

        response = client.patch(
            f"/provider-schedule/{sr.id}/start-travel",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 409

    def test_success_returns_200_with_correct_fields(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/start-travel",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["service_request_id"] == str(sr.id)
        assert body["status"] == ServiceRequestStatus.IN_TRANSIT.value
        assert body["travel_started_at"] is not None
        assert body["estimated_arrival_at"] is not None
        assert body["travel_duration_minutes"] is not None
        assert "travel_distance_km" in body

    def test_success_transitions_to_in_transit(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/start-travel",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 200

        # Verify state was persisted
        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.IN_TRANSIT.value
        assert updated.travel_started_at is not None
        assert updated.route_calculated_at is not None
        assert updated.estimated_arrival_at is not None
        assert updated.travel_duration_minutes is not None

    def test_second_call_returns_409_concurrency(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Segunda chamada retorna 409 pois status já é IN_TRANSIT."""
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)
        headers = _make_auth_header(provider)
        url = f"/provider-schedule/{sr.id}/start-travel"

        r1 = client.patch(url, headers=headers)
        assert r1.status_code == 200

        r2 = client.patch(url, headers=headers)
        assert r2.status_code == 409

    def test_returns_500_when_logistics_acl_fails_and_state_remains_confirmed(
        self, client, tst_db_session, make_user, make_service, seed_roles, monkeypatch
    ):
        import infrastructure.api.routers.provider_schedule_router as provider_schedule_router
        from usecases.service_request.start_provider_travel.start_provider_travel_usecase import (
            StartProviderTravelUseCase,
        )

        class FailingLogisticsGateway:
            def estimate_route(self, origin_address, destination_address, departure_at):
                raise RuntimeError("ACL logística indisponível")

        def fake_factory(session):
            return StartProviderTravelUseCase(
                service_request_repository=ServiceRequestRepository(session=session),
                logistics_acl_gateway=FailingLogisticsGateway(),
                notification_gateway=None,
            )

        monkeypatch.setattr(
            provider_schedule_router,
            "make_start_provider_travel_usecase",
            fake_factory,
        )

        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com", roles={"prestador"},
        )
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com", roles={"cliente"},
        )
        svc = _add_service(tst_db_session, make_service)

        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/start-travel",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 500

        persisted = ServiceRequestRepository(session=tst_db_session).find_by_id(sr.id)
        assert persisted.status == ServiceRequestStatus.CONFIRMED.value
        assert persisted.travel_started_at is None
        assert persisted.route_calculated_at is None
        assert persisted.estimated_arrival_at is None
        assert persisted.travel_duration_minutes is None
