from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestListAvailableServiceRequestsForProviderRoute:
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

    def test_requires_auth(self, client):
        response = client.get("/provider-service-requests/available")

        assert response.status_code == 401

    def test_forbidden_for_cliente(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        cliente = make_user(
            id=uuid4(),
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(cliente)
        session.commit()

        headers = self._make_auth_header(cliente)

        response = client.get(
            "/provider-service-requests/available",
            headers=headers,
        )

        assert response.status_code == 403

    def test_success(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        make_provider_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        service_request_repository = ServiceRequestRepository(session=session)

        provider_1 = make_user(
            id=uuid4(),
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        provider_2 = make_user(
            id=uuid4(),
            name="Prestador 2",
            email="prestador2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        client_user = make_user(
            id=uuid4(),
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )

        user_repository.add_user(provider_1)
        user_repository.add_user(provider_2)
        user_repository.add_user(client_user)

        service_1 = make_service(
            id=uuid4(),
            name="manicure em gel",
            description="Serviço de manicure em gel",
        )
        service_2 = make_service(
            id=uuid4(),
            name="depilação de cilios",
            description="Serviço de depilação",
        )

        service_repository.create_service(service_1)
        service_repository.create_service(service_2)
        session.commit()

        provider_service_1 = make_provider_service(
            provider_id=provider_1.id,
            service_id=service_1.id,
            price=Decimal("150.00"),
            active=True,
        )
        provider_service_2 = make_provider_service(
            provider_id=provider_2.id,
            service_id=service_2.id,
            price=Decimal("200.00"),
            active=True,
        )

        provider_service_repository.create_provider_service(provider_service_1)
        provider_service_repository.create_provider_service(provider_service_2)
        session.commit()

        request_for_provider_1 = ServiceRequest(
            id=uuid4(),
            client_id=client_user.id,
            service_id=service_1.id,
            desired_datetime=datetime(2026, 4, 10, 14, 0, 0),
            address="Rua A, 123",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            created_at=datetime(2026, 4, 4, 10, 0, 0),
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        request_for_provider_2 = ServiceRequest(
            id=uuid4(),
            client_id=client_user.id,
            service_id=service_2.id,
            desired_datetime=datetime(2026, 4, 11, 15, 0, 0),
            address="Rua B, 456",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            created_at=datetime(2026, 4, 4, 11, 0, 0),
            expires_at=datetime.utcnow() + timedelta(days=2),
        )

        service_request_repository.create(request_for_provider_1)
        service_request_repository.create(request_for_provider_2)
        session.commit()

        headers = self._make_auth_header(provider_1)

        response = client.get(
            "/provider-service-requests/available",
            headers=headers,
        )

        assert response.status_code == 200

        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1

        item = body[0]

        assert item["service_request_id"] == str(request_for_provider_1.id)
        assert item["client_id"] == str(client_user.id)
        assert item["service_id"] == str(service_1.id)
        assert item["service_name"] == "Manicure Em Gel"
        assert item["service_description"] == "Serviço de manicure em gel"
        assert item["address"] == "Rua A, 123"
        assert item["status"] == "AWAITING_PROVIDER_ACCEPTANCE"
        assert item["provider_service_id"] == str(provider_service_1.id)
        assert Decimal(str(item["price"])) == Decimal("150.00")

        assert item["desired_datetime"] == "2026-04-10T14:00:00"
        assert item["created_at"] == "2026-04-04T10:00:00"
        assert item["expires_at"] is not None
    def test_list_available_service_requests_returns_500_on_unexpected_error(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        from unittest.mock import patch
        session = tst_db_session
        from infrastructure.user.sqlalchemy.user_repository import userRepository
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            email=f"provider.err.{uuid4().hex}@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        headers = self._make_auth_header(provider)

        with patch(
            "infrastructure.api.routers.provider_service_request_routers.make_list_available_service_requests_for_provider_usecase",
            side_effect=RuntimeError("unexpected error"),
        ):
            response = client.get("/provider-service-requests/available", headers=headers)

        assert response.status_code == 500