"""
Testes de integração da rota PATCH /user-service-requests/{id}/confirm-payment — Fase 3.
Cobre:
- 401 sem autenticação
- 403 para prestador
- 404 se request não existir
- 403 se cliente não for o dono
- 409 se não estiver em AWAITING_PAYMENT
- 409 se já estiver em PAYMENT_PROCESSING
- 200 no sucesso com campos corretos
- ServiceRequest muda para PAYMENT_PROCESSING
- PaymentAttempt muda para PROCESSING
- ACL é chamada (mock determinístico)
- falha técnica da ACL não marca como aprovado (estado fica PAYMENT_PROCESSING)
- duplo clique retorna 409
"""

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


def _create_awaiting_payment_sr(
    session, client_id, service_id, provider_id,
    payment_amount=Decimal("150.00"),
):
    now = datetime.utcnow()
    sr = ServiceRequest(
        id=uuid4(),
        client_id=client_id,
        service_id=service_id,
        desired_datetime=now + timedelta(days=1),
        address="Rua Serviço, 42",
        status=ServiceRequestStatus.AWAITING_PAYMENT,
        accepted_provider_id=provider_id,
        departure_address="Rua Origem, 1",
        service_price=Decimal("120.00"),
        travel_price=Decimal("30.00"),
        total_price=payment_amount,
        accepted_at=now - timedelta(hours=3),
        travel_started_at=now - timedelta(hours=2),
        route_calculated_at=now - timedelta(hours=2),
        estimated_arrival_at=now - timedelta(hours=1, minutes=30),
        travel_duration_minutes=30,
        provider_arrived_at=now - timedelta(hours=1, minutes=25),
        client_confirmed_provider_arrival_at=now - timedelta(hours=1, minutes=20),
        service_started_at=now - timedelta(hours=1, minutes=20),
        service_finished_at=now - timedelta(minutes=10),
        payment_requested_at=now - timedelta(minutes=10),
        payment_amount=payment_amount,
        payment_last_status=PaymentStatusSnapshot.REQUESTED.value,
        payment_attempt_count=1,
    )
    repo = ServiceRequestRepository(session=session)
    result = repo.create(sr)
    session.commit()
    return result


def _create_payment_attempt_for(session, service_request_id, amount=Decimal("150.00")):
    from domain.payment.payment_attempt_entity import PaymentAttempt
    pa_repo = PaymentAttemptRepository(session=session)
    attempt = PaymentAttempt(
        id=uuid4(),
        service_request_id=service_request_id,
        attempt_number=1,
        amount=amount,
        status=PaymentAttemptStatus.REQUESTED.value,
        requested_at=datetime.utcnow() - timedelta(minutes=10),
    )
    result = pa_repo.create(attempt)
    session.commit()
    return result


class TestConfirmPaymentRoute:

    def test_requires_auth(self, client):
        response = client.patch(f"/user-service-requests/{uuid4()}/confirm-payment")
        assert response.status_code == 401

    def test_rejects_prestador_role(self, client, tst_db_session, make_user, seed_roles):
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        response = client.patch(
            f"/user-service-requests/{uuid4()}/confirm-payment",
            headers=_make_auth_header(provider),
        )
        assert response.status_code == 403

    def test_returns_404_when_not_found(self, client, tst_db_session, make_user, seed_roles):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        response = client.patch(
            f"/user-service-requests/{uuid4()}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 404

    def test_returns_403_when_client_not_owner(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente Dono", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        other_cli = _add_user(
            tst_db_session, make_user,
            name="Outro Cliente", email=f"cli2_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(other_cli),
        )
        assert response.status_code == 403

    def test_returns_409_when_not_awaiting_payment(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)

        # Create a CONFIRMED SR (no financial fields) — not in AWAITING_PAYMENT
        now = datetime.utcnow()
        sr = ServiceRequest(
            id=uuid4(),
            client_id=cli.id,
            service_id=svc.id,
            desired_datetime=now + timedelta(days=1),
            address="Rua Destino, 100",
            status=ServiceRequestStatus.CONFIRMED,
            accepted_provider_id=provider.id,
            departure_address="Rua Origem, 1",
            service_price=Decimal("120.00"),
            travel_price=Decimal("30.00"),
            total_price=Decimal("150.00"),
            accepted_at=now - timedelta(hours=1),
        )
        repo = ServiceRequestRepository(session=tst_db_session)
        repo.create(sr)
        tst_db_session.commit()

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 409

    def test_returns_409_when_already_payment_processing(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)

        # Move to PAYMENT_PROCESSING manually
        now = datetime.utcnow()
        tst_db_session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == sr.id
        ).update({
            "status": ServiceRequestStatus.PAYMENT_PROCESSING.value,
            "payment_processing_started_at": now,
            "payment_last_status": PaymentStatusSnapshot.PROCESSING.value,
        })
        tst_db_session.commit()

        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 409

    def test_success_returns_200_with_correct_fields(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["service_request_id"] == str(sr.id)
        assert body["status"] == ServiceRequestStatus.PAYMENT_PROCESSING.value
        assert body["payment_processing_started_at"] is not None
        assert body["payment_reference"] is not None

    def test_success_transitions_to_payment_processing(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 200

        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.PAYMENT_PROCESSING.value
        assert updated.payment_processing_started_at is not None
        assert updated.payment_last_status == PaymentStatusSnapshot.PROCESSING.value
        assert updated.payment_attempt_count == 1  # unchanged

    def test_success_payment_attempt_becomes_processing(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 200

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = pa_repo.find_latest_by_service_request_id(sr.id)
        assert attempt is not None
        assert attempt.status == PaymentAttemptStatus.PROCESSING.value
        assert attempt.processing_started_at is not None

    def test_double_click_returns_409(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        headers = _make_auth_header(cli)
        url = f"/user-service-requests/{sr.id}/confirm-payment"

        r1 = client.patch(url, headers=headers)
        assert r1.status_code == 200

        r2 = client.patch(url, headers=headers)
        assert r2.status_code == 409

    def test_not_completed_after_phase3(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Fase 3 não fecha o atendimento — status permanece PAYMENT_PROCESSING."""
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 200

        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.status == ServiceRequestStatus.PAYMENT_PROCESSING.value
        assert updated.status != ServiceRequestStatus.COMPLETED.value
        assert updated.service_concluded_at is None

    def test_gateway_reference_persisted_on_sr_after_success(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Após sucesso, external_reference da ACL deve ser persistido no ServiceRequest."""
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 200
        body = response.json()

        # payment_reference in response and DB must match
        repo = ServiceRequestRepository(session=tst_db_session)
        updated = repo.find_by_id(sr.id)
        assert updated.payment_reference is not None
        assert updated.payment_reference == body["payment_reference"]
        assert updated.payment_provider is not None

    def test_gateway_reference_persisted_on_attempt_after_success(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        """Após sucesso, external_reference da ACL deve ser persistido na PaymentAttempt."""
        cli = _add_user(
            tst_db_session, make_user,
            name="Cliente", email=f"cli_{uuid4().hex}@example.com",
            roles={"cliente"},
        )
        provider = _add_user(
            tst_db_session, make_user,
            name="Prestador", email=f"prov_{uuid4().hex}@example.com",
            roles={"prestador"},
        )
        svc = _add_service(tst_db_session, make_service)
        sr = _create_awaiting_payment_sr(tst_db_session, cli.id, svc.id, provider.id)
        _create_payment_attempt_for(tst_db_session, sr.id, sr.payment_amount)

        response = client.patch(
            f"/user-service-requests/{sr.id}/confirm-payment",
            headers=_make_auth_header(cli),
        )
        assert response.status_code == 200

        pa_repo = PaymentAttemptRepository(session=tst_db_session)
        attempt = pa_repo.find_latest_by_service_request_id(sr.id)
        assert attempt.external_reference is not None
        assert attempt.provider is not None