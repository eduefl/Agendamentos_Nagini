from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import ServiceRequest
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestListMyServiceRequestsRoute:
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

    def test_list_my_service_requests_requires_auth(self, client):
        response = client.get("/user-service-requests/me")

        assert response.status_code == 401

    def test_list_my_service_requests_forbidden_for_prestador(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        prestador = make_user(
            id=uuid4(),
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(prestador)
        session.commit()

        headers = self._make_auth_header(prestador)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 403

    def test_list_my_service_requests_success_returns_only_logged_client_requests(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        service_request_repository = ServiceRequestRepository(session=session)

        client_1 = make_user(
            id=uuid4(),
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        client_2 = make_user(
            id=uuid4(),
            name="Cliente 2",
            email="cliente2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )

        user_repository.add_user(client_1)
        user_repository.add_user(client_2)

        service_1 = make_service(
            id=uuid4(),
            name="DEPILAÇÃO DE CILIOS",
            description="Serviço de depilação",
        )
        service_2 = make_service(
            id=uuid4(),
            name="manicure em gel",
            description="Serviço de manicure em gel",
        )
        service_3 = make_service(
            id=uuid4(),
            name="servico de taxi",
            description="Serviço de transporte",
        )

        service_repository.create_service(service_1)
        service_repository.create_service(service_2)
        service_repository.create_service(service_3)
        session.commit()

        request_1 = ServiceRequest(
            id=uuid4(),
            client_id=client_1.id,
            service_id=service_1.id,
            desired_datetime=datetime(2026, 4, 2, 10, 0, 0),
            address="Rua A, 123",
            created_at=datetime(2026, 4, 1, 8, 0, 0),
        )
        request_2 = ServiceRequest(
            id=uuid4(),
            client_id=client_1.id,
            service_id=service_2.id,
            desired_datetime=datetime(2026, 4, 3, 14, 0, 0),
            address="Rua B, 456",
            created_at=datetime(2026, 4, 1, 9, 0, 0),
        )
        request_3 = ServiceRequest(
            id=uuid4(),
            client_id=client_2.id,
            service_id=service_3.id,
            desired_datetime=datetime(2026, 4, 4, 16, 0, 0),
            address="Rua C, 789",
            created_at=datetime(2026, 4, 1, 10, 0, 0),
        )

        service_request_repository.create(request_1)
        service_request_repository.create(request_2)
        service_request_repository.create(request_3)
        session.commit()

        headers = self._make_auth_header(client_1)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 2

        returned_ids = {item["service_request_id"] for item in body}
        assert returned_ids == {str(request_1.id), str(request_2.id)}

        # valida ordenação: mais recente primeiro
        assert body[0]["service_request_id"] == str(request_2.id)
        assert body[1]["service_request_id"] == str(request_1.id)

        assert body[0]["client_id"] == str(client_1.id)
        assert body[0]["service_id"] == str(service_2.id)
        assert body[0]["service_name"] == "Manicure Em Gel"
        assert body[0]["service_description"] == "Serviço de manicure em gel"
        assert body[0]["status"] == "REQUESTED"
        assert body[0]["address"] == "Rua B, 456"

        assert body[1]["client_id"] == str(client_1.id)
        assert body[1]["service_id"] == str(service_1.id)
        assert body[1]["service_name"] == "Depilação de Cilios"
        assert body[1]["service_description"] == "Serviço de depilação"
        assert body[1]["status"] == "REQUESTED"
        assert body[1]["address"] == "Rua A, 123"

    def test_list_my_service_requests_returns_null_prices_before_provider_acceptance(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        service_request_repository = ServiceRequestRepository(session=session)

        client_user = make_user(
            id=uuid4(),
            name="Cliente Sem Aceite",
            email="cliente.sem.aceite@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_user)

        service = make_service(
            id=uuid4(),
            name="Instalação",
            description="Instalação técnica",
        )
        service_repository.create_service(service)
        session.commit()

        request = ServiceRequest(
            id=uuid4(),
            client_id=client_user.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            status="AWAITING_PROVIDER_ACCEPTANCE",
            address="Rua Sem Aceite, 50",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        service_request_repository.create(request)
        session.commit()

        headers = self._make_auth_header(client_user)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(request.id)
        assert body[0]["accepted_provider_id"] is None
        assert body[0]["service_price"] is None
        assert body[0]["travel_price"] is None
        assert body[0]["total_price"] is None
        assert body[0]["status"] == "AWAITING_PROVIDER_ACCEPTANCE"

    def test_list_my_service_requests_returns_prices_filled_after_confirmation(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        service_request_repository = ServiceRequestRepository(session=session)

        client_user = make_user(
            id=uuid4(),
            name="Cliente Confirmado",
            email="cliente.confirmado@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        provider_user = make_user(
            id=uuid4(),
            name="Prestador Confirmado",
            email="prestador.confirmado@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(client_user)
        user_repository.add_user(provider_user)

        service = make_service(
            id=uuid4(),
            name="Visita Técnica",
            description="Visita técnica residencial",
        )
        service_repository.create_service(service)
        session.commit()

        confirmed_request = ServiceRequest(
            id=uuid4(),
            client_id=client_user.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=3),
            status="CONFIRMED",
            address="Rua Confirmada, 77",
            accepted_provider_id=provider_user.id,
            departure_address="Rua Origem, 12",
            service_price=Decimal("200.00"),
            travel_price=Decimal("35.00"),
            total_price=Decimal("235.00"),
            accepted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        service_request_repository.create(confirmed_request)
        session.commit()

        headers = self._make_auth_header(client_user)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(confirmed_request.id)
        assert body[0]["accepted_provider_id"] == str(provider_user.id)
        assert Decimal(str(body[0]["service_price"])) == Decimal("200.00")
        assert Decimal(str(body[0]["travel_price"])) == Decimal("35.00")
        assert Decimal(str(body[0]["total_price"])) == Decimal("235.00")
        assert body[0]["status"] == "CONFIRMED"

    def test_list_my_service_requests_returns_only_requests_from_logged_client(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        service_request_repository = ServiceRequestRepository(session=session)

        client_a = make_user(
            id=uuid4(),
            name="Cliente A",
            email="cliente.a@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        client_b = make_user(
            id=uuid4(),
            name="Cliente B",
            email="cliente.b@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_a)
        user_repository.add_user(client_b)

        service_a = make_service(
            id=uuid4(),
            name="Corte de cabelo",
            description="Serviço do cliente A",
        )
        service_b = make_service(
            id=uuid4(),
            name="Limpeza",
            description="Serviço do cliente B",
        )
        service_repository.create_service(service_a)
        service_repository.create_service(service_b)
        session.commit()

        request_a = ServiceRequest(
            id=uuid4(),
            client_id=client_a.id,
            service_id=service_a.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua Cliente A, 10",
            created_at=datetime(2026, 4, 1, 8, 0, 0),
        )
        request_b = ServiceRequest(
            id=uuid4(),
            client_id=client_b.id,
            service_id=service_b.id,
            desired_datetime=datetime.utcnow() + timedelta(days=2),
            address="Rua Cliente B, 20",
            created_at=datetime(2026, 4, 1, 9, 0, 0),
        )
        service_request_repository.create(request_a)
        service_request_repository.create(request_b)
        session.commit()

        headers = self._make_auth_header(client_a)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["service_request_id"] == str(request_a.id)
        assert body[0]["client_id"] == str(client_a.id)
        assert all(item["client_id"] == str(client_a.id) for item in body)
        assert str(request_b.id) not in {item["service_request_id"] for item in body}

    def test_list_my_service_requests_returns_empty_list_when_client_has_no_requests(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        client_user = make_user(
            id=uuid4(),
            name="Cliente Sem Solicitações",
            email="cliente.sem.solicitacoes@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_user)
        session.commit()

        headers = self._make_auth_header(client_user)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_my_service_requests_forbidden_for_inactive_cliente(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        inactive_client = make_user(
            id=uuid4(),
            name="Cliente Inativo",
            email="inactive.client@example.com",
            hashed_password="hashed_password",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(inactive_client)
        session.commit()

        headers = self._make_auth_header(inactive_client)

        response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 403

    def test_list_my_service_requests_returns_500_on_unexpected_error(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        client_user = make_user(
            id=uuid4(),
            name="Cliente Erro",
            email=f"cliente.erro.{uuid4().hex}@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_user)
        session.commit()

        headers = self._make_auth_header(client_user)

        with patch(
            "infrastructure.api.routers.service_request_routers.make_list_my_service_requests_usecase",
            side_effect=RuntimeError("unexpected error"),
        ):
            response = client.get("/user-service-requests/me", headers=headers)

        assert response.status_code == 500