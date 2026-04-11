from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_status_snapshot import PaymentStatusSnapshot
from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.payment.sqlalchemy.payment_attempt_repository import (
    PaymentAttemptRepository,
)
from infrastructure.security.factories.make_token_service import make_token_service
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


def _create_in_progress_sr(session, client_id, service_id, provider_id, total_price=Decimal("150.00")):
    now = datetime.utcnow()
    sr = ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Serviço, 42",
        status=ServiceRequestStatus.IN_PROGRESS,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("120.00"),
        travel_price=Decimal("30.00"),
        total_price=total_price,
        accepted_at=now - timedelta(hours=2),
        travel_started_at=now - timedelta(hours=1),
        route_calculated_at=now - timedelta(hours=1),
        estimated_arrival_at=now - timedelta(minutes=30),
        travel_duration_minutes=30,
        provider_arrived_at=now - timedelta(minutes=25),
        client_confirmed_provider_arrival_at=now - timedelta(minutes=20),
        service_started_at=now - timedelta(minutes=20),
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


class TestFinishServiceRoute:
    def test_requires_auth(self, client):
        response = client.patch(f"/provider-schedule/{uuid4()}/finish-service")
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
            f"/provider-schedule/{uuid4()}/finish-service",
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
            f"/provider-schedule/{uuid4()}/finish-service",
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(other_provider),
        )
        assert response.status_code == 403

    def test_returns_409_when_status_not_in_progress(
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
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 409

    def test_returns_409_when_already_in_awaiting_payment(
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        now = datetime.utcnow()
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update(
            {
                "status": ServiceRequestStatus.AWAITING_PAYMENT.value,
                "service_finished_at": now,
                "payment_requested_at": now,
            }
        )
        tst_db_session.commit()

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 409

    def test_returns_409_when_already_completed(
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        # Force status to AWAITING_PAYMENT first, then COMPLETED with all required fields
        now = datetime.utcnow()
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update(
            {
                "status": ServiceRequestStatus.COMPLETED.value,
                "service_finished_at": now - timedelta(minutes=10),
                "payment_requested_at": now - timedelta(minutes=10),
                "payment_processing_started_at": now - timedelta(minutes=5),
                "payment_approved_at": now - timedelta(minutes=1),
                "service_concluded_at": now,
                "payment_last_status": "APPROVED",
                "payment_amount": Decimal("150.00"),
                "payment_attempt_count": 1,
            }
        )
        tst_db_session.commit()

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["service_request_id"] == str(sr.id)
        assert body["status"] == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert body["service_finished_at"] is not None
        assert body["payment_requested_at"] is not None
        assert body["payment_amount"] is not None
        assert body["payment_last_status"] == PaymentStatusSnapshot.REQUESTED.value

    def test_success_transitions_to_awaiting_payment(
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 200

        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.AWAITING_PAYMENT.value
        assert updated.service_finished_at is not None
        assert updated.payment_requested_at is not None
        assert updated.payment_amount is not None
        assert updated.payment_last_status == PaymentStatusSnapshot.REQUESTED.value
        assert updated.payment_attempt_count == 1
        assert updated.service_concluded_at is None

    def test_success_creates_payment_attempt(
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 200

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = pa_repo.find_latest_by_service_request_id(sr.id)
        assert attempt is not None
        assert attempt.attempt_number == 1
        assert attempt.status == PaymentAttemptStatus.REQUESTED.value
        assert attempt.external_reference is None

    def test_second_call_returns_409_concurrency(
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        headers = _make_auth_header(provider)
        url = f"/provider-schedule/{sr.id}/finish-service"

        r1 = client.patch(url, headers=headers)
        assert r1.status_code == 200

        r2 = client.patch(url, headers=headers)
        assert r2.status_code == 409

    def test_no_acl_call_in_this_phase(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Fase 2 não deve chamar nenhuma ACL de pagamento externo."""
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
        sr = _create_in_progress_sr(tst_db_session, cli.id, svc.id, provider.id)

        response = client.patch(
            f"/provider-schedule/{sr.id}/finish-service",
            headers=_make_auth_header(provider),
        )

        assert response.status_code == 200
        # payment_reference and payment_provider remain None — no ACL was called
        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.payment_reference is None
        assert updated.payment_provider is None
        assert updated.status != ServiceRequestStatus.PAYMENT_PROCESSING.value

    def test_returns_409_when_final_amount_is_invalid(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Valor final do atendimento zero ou não materializável → 409 Conflict."""
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

        # Create an IN_PROGRESS SR with total_price = 0 (service_price + travel_price = 0)
        # Entity validation passes because 0 + 0 == 0; use case raises ServiceRequestInvalidFinalAmountError
        now = datetime.utcnow()
        sr_zero = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Serviço, 42",
            status=ServiceRequestStatus.IN_PROGRESS,
            accepted_provider_id=provider.id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("0"),
            travel_price=Decimal("0"),
            total_price=Decimal("0"),
            accepted_at=now - timedelta(hours=2),
            travel_started_at=now - timedelta(hours=1),
            route_calculated_at=now - timedelta(hours=1),
            estimated_arrival_at=now - timedelta(minutes=30),
            travel_duration_minutes=30,
            provider_arrived_at=now - timedelta(minutes=25),
            client_confirmed_provider_arrival_at=now - timedelta(minutes=20),
            service_started_at=now - timedelta(minutes=20),
        )
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr_zero)
        tst_db_session.commit()

        response = client.patch(
            f"/provider-schedule/{sr_zero.id}/finish-service",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 409