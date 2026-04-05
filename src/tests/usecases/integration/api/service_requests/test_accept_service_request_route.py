from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.security.token_service_dto import CreateAccessTokenDTO
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service_request.sqlalchemy.service_request_model import ServiceRequestModel
from infrastructure.user.sqlalchemy.user_repository import userRepository
from domain.service_request.service_request_entity import ServiceRequestStatus


class TestAcceptServiceRequestRoute:
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

    def _create_user(self, session, make_user, roles, email=None):
        repo = userRepository(session=session)
        user = make_user(
            id=uuid4(),
            email=email or f"{uuid4().hex}@example.com",
            roles=roles,
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
        )
        repo.add_user(user)
        return user

    def _create_available_service_request(self, session, client_id, service_id, provider_id=None, provider_price=None):
        service_model = session.query(ServiceModel).filter(ServiceModel.id == service_id).first()
        assert service_model is not None, "Service not found"

        sr = ServiceRequestModel(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua Destino, 100",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
        )
        session.add(sr)
        session.flush()

        if provider_id and provider_price:
            ps = ProviderServiceModel(
                id=uuid4(),
                provider_id=provider_id,
                service_id=service_id,
                price=provider_price,
                active=True,
            )
            session.add(ps)

        session.commit()
        return sr

    def test_accept_requires_auth(self, client):
        response = client.patch(
            f"/service-requests/{uuid4()}/accept",
            json={"departure_address": "Rua Saída, 1"},
        )
        assert response.status_code == 401

    def test_accept_rejects_client(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        headers = self._make_auth_header(client_user)

        response = client.patch(
            f"/service-requests/{uuid4()}/accept",
            headers=headers,
            json={"departure_address": "Rua Saída, 1"},
        )
        assert response.status_code == 403

    def test_accept_returns_404_when_request_not_found(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        provider = self._create_user(session, make_user, {"prestador"})
        headers = self._make_auth_header(provider)

        response = client.patch(
            f"/service-requests/{uuid4()}/accept",
            headers=headers,
            json={"departure_address": "Rua Saída, 1"},
        )
        assert response.status_code == 404

    def test_accept_returns_422_when_provider_does_not_serve_service(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"Srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        # No ProviderService binding for this provider
        sr = self._create_available_service_request(session, client_user.id, service.id)

        headers = self._make_auth_header(provider)
        response = client.patch(
            f"/service-requests/{sr.id}/accept",
            headers=headers,
            json={"departure_address": "Rua Saída, 1"},
        )
        assert response.status_code == 422

    def test_accept_success(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"Srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        sr = self._create_available_service_request(
            session, client_user.id, service.id,
            provider_id=provider.id,
            provider_price=Decimal("100.00"),
        )

        headers = self._make_auth_header(provider)
        response = client.patch(
            f"/service-requests/{sr.id}/accept",
            headers=headers,
            json={"departure_address": "Rua Saída, 123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ServiceRequestStatus.CONFIRMED.value
        assert body["accepted_provider_id"] == str(provider.id)
        assert "service_price" in body
        assert "travel_price" in body
        assert "total_price" in body
        assert "accepted_at" in body
        #  The approx function is used here with an absolute tolerance of 0.01, which means the assertion will pass as long as the difference between the calculated 
        # sum and the reported total price is less than or equal to 0.01. This
        #  is a common practice when dealing with floating-point numbers, as small rounding errors can occur during calculations.        
        assert float(body["total_price"]) == pytest.approx(
            float(body["service_price"]) + float(body["travel_price"]), abs=0.01
        )        

    def test_accept_returns_409_when_already_accepted_by_another(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider1 = self._create_user(session, make_user, {"prestador"})
        provider2 = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"Srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        sr = self._create_available_service_request(
            session, client_user.id, service.id,
            provider_id=provider1.id,
            provider_price=Decimal("100.00"),
        )

        # Add provider_service for provider2 as well
        ps2 = ProviderServiceModel(
            id=uuid4(),
            provider_id=provider2.id,
            service_id=service.id,
            price=Decimal("90.00"),
            active=True,
        )
        session.add(ps2)
        session.commit()

        headers1 = self._make_auth_header(provider1)
        headers2 = self._make_auth_header(provider2)

        # Provider1 accepts successfully
        r1 = client.patch(
            f"/service-requests/{sr.id}/accept",
            headers=headers1,
            json={"departure_address": "Rua A, 1"},
        )
        assert r1.status_code == 200

        # Provider2 tries to accept the same request
        r2 = client.patch(
            f"/service-requests/{sr.id}/accept",
            headers=headers2,
            json={"departure_address": "Rua B, 2"},
        )
        assert r2.status_code == 409

    def test_accept_returns_409_when_request_unavailable(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"Srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        # Create request with expired time
        sr = ServiceRequestModel(
            id=uuid4(),
            client_id=client_user.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua Destino, 100",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() - timedelta(minutes=5),  # already expired
            created_at=datetime.utcnow(),
        )
        session.add(sr)
        ps = ProviderServiceModel(
            id=uuid4(),
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )
        session.add(ps)
        session.commit()

        headers = self._make_auth_header(provider)
        response = client.patch(
            f"/service-requests/{sr.id}/accept",
            headers=headers,
            json={"departure_address": "Rua Saída, 1"},
        )
        assert response.status_code == 409

    def test_accept_response_contains_correct_prices(self, client, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"Srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        service_price = Decimal("200.00")
        sr = self._create_available_service_request(
            session, client_user.id, service.id,
            provider_id=provider.id,
            provider_price=service_price,
        )

        headers = self._make_auth_header(provider)
        response = client.patch(
            f"/service-requests/{sr.id}/accept",
            headers=headers,
            json={"departure_address": "Rua Saída, 999"},
        )

        assert response.status_code == 200
        body = response.json()
        assert float(body["service_price"]) == float(service_price)
        # total = service + travel (travel is mocked, just check consistency)
        assert float(body["total_price"]) == pytest.approx(
            float(body["service_price"]) + float(body["travel_price"]), abs=0.01
        )