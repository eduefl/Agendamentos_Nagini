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


def _create_arrived_sr(session, client_id, service_id, provider_id):
    now = datetime.utcnow()
    sr = ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Destino, 100",
        status=ServiceRequestStatus.ARRIVED,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("100.00"),
        travel_price=Decimal("20.00"),
        total_price=Decimal("120.00"),
        accepted_at=now - timedelta(hours=1),
        travel_started_at=now - timedelta(minutes=30),
        route_calculated_at=now - timedelta(minutes=30),
        estimated_arrival_at=now - timedelta(minutes=5),
        travel_duration_minutes=25,
        provider_arrived_at=now - timedelta(minutes=5),
    )
    repo = ServiceRequestRepository(session=session)
    result = repo.create(sr)
    session.commit()
    return result


def _create_confirmed_sr(session, client_id, service_id, provider_id):
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
    )
    repo = ServiceRequestRepository(session=session)
    result = repo.create(sr)
    session.commit()
    return result


class TestConfirmProviderArrivalRoute:
    def test_requires_auth(self, client):
        response = client.patch(
            f"/user-service-requests/{uuid4()}/confirm-provider-arrival"
        )
        assert response.status_code == 401

    def test_rejects_provider_role(self, client, tst_db_session, make_user, seed_roles):
        provider_user = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        response = client.patch(
            f"/user-service-requests/{uuid4()}/confirm-provider-arrival",
            headers=_make_auth_header(provider_user),
        )
        assert response.status_code == 403

    def test_returns_404_when_not_found(
        self, client, tst_db_session, make_user, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        response = client.patch(
            f"/user-service-requests/{uuid4()}/confirm-provider-arrival",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 404

    def test_returns_403_when_client_not_owner(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente Dono",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        other_cli = _add_user(
            tst_db_session,
            make_user,
            name="Outro Cliente",
            email=f"cli2_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_arrived_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-provider-arrival",
            headers=_make_auth_header(other_cli),
        )
        assert response.status_code == 403

    def test_returns_409_when_status_not_arrived(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_confirmed_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-provider-arrival",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 409

    def test_returns_409_when_already_in_progress(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_arrived_sr(tst_db_session, cli.id, svc.id, provider.id)

        now = datetime.utcnow()
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update(
            {
                "status": ServiceRequestStatus.IN_PROGRESS.value,
                "client_confirmed_provider_arrival_at": now,
                "service_started_at": now,
            }
        )
        tst_db_session.commit()

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-provider-arrival",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 409

    def test_success_returns_200_with_correct_fields(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_arrived_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-provider-arrival",
            headers=_make_auth_header(cli),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["service_request_id"] == str(sr.id)
        assert body["status"] == ServiceRequestStatus.IN_PROGRESS.value
        assert body["client_confirmed_provider_arrival_at"] is not None
        assert body["service_started_at"] is not None

    def test_success_transitions_to_in_progress(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_arrived_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-provider-arrival",
            headers=_make_auth_header(cli),
        )

        assert response.status_code == 200

        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.IN_PROGRESS.value
        assert updated.client_confirmed_provider_arrival_at is not None
        assert updated.service_started_at is not None

    def test_second_call_returns_409_concurrency(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session,
            make_user,
            name="Cliente",
            email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session,
            make_user,
            name="Prestador",
            email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_arrived_sr(tst_db_session, cli.id, svc.id, provider.id)

        headers = _make_auth_header(cli)
        url = f"/user-service-requests/{sr.id}/confirm-provider-arrival"

        r1 = client.patch(url, headers=headers)
        assert r1.status_code == 200

        r2 = client.patch(url, headers=headers)
        assert r2.status_code == 409