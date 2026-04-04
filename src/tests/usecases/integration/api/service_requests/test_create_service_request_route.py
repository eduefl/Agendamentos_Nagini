from datetime import datetime, timedelta
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestCreateServiceRequestRoute:
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

    def test_create_service_request_requires_auth(self, client):
        response = client.post(
            "/service-requests/",
            json={
                "service_id": str(uuid4()),
                "desired_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "address": "Rua X, 123",
            },
        )

        assert response.status_code == 401

    def test_create_service_request_rejects_non_client(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider_user = make_user(
            id=uuid4(),
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider_user)
        session.commit()

        headers = self._make_auth_header(provider_user)

        response = client.post(
            "/service-requests/",
            headers=headers,
            json={
                "service_id": str(uuid4()),
                "desired_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "address": "Rua X, 123",
            },
        )

        assert response.status_code == 403

    def test_create_service_request_success(
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
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_user)

        service = ServiceModel(
            id=uuid4(),
            name="Corte de cabelo",
            description="Corte masculino",
        )
        session.add(service)
        session.commit()

        headers = self._make_auth_header(client_user)

        desired_datetime = datetime.utcnow() + timedelta(days=1)

        response = client.post(
            "/service-requests/",
            headers=headers,
            json={
                "service_id": str(service.id),
                "desired_datetime": desired_datetime.isoformat(),
                "address": "Rua das Flores, 123",
            },
        )

        assert response.status_code == 201

        body = response.json()
        assert "service_request_id" in body
        assert body["client_id"] == str(client_user.id)
        assert body["service_id"] == str(service.id)
        assert body["status"] == "AWAITING_PROVIDER_ACCEPTANCE"
        assert body["address"] == "Rua das Flores, 123"
        assert body["desired_datetime"] is not None
        assert body["created_at"] is not None

    def test_create_service_request_returns_404_when_service_not_found(
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
            name="Cliente 2",
            email="cliente2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_user)
        session.commit()

        headers = self._make_auth_header(client_user)

        response = client.post(
            "/service-requests/",
            headers=headers,
            json={
                "service_id": str(uuid4()),
                "desired_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "address": "Rua A, 100",
            },
        )

        assert response.status_code == 404
        body = response.json()
        assert "Service" in body["detail"]
        assert "not found" in body["detail"]
        
        

    def test_create_service_request_returns_422_when_desired_datetime_is_in_past(
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
            name="Cliente 3",
            email="cliente3@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client_user)

        service = ServiceModel(
            id=uuid4(),
            name="Manicure",
            description="Manicure simples",
        )
        session.add(service)
        session.commit()

        headers = self._make_auth_header(client_user)

        response = client.post(
            "/service-requests/",
            headers=headers,
            json={
                "service_id": str(service.id),
                "desired_datetime": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                "address": "Rua B, 200",
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["detail"] == "Desired datetime must be in the future"
