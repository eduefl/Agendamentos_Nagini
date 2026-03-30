from decimal import Decimal
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO

from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestCreateProviderServiceRoute:
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

        access_token = token_service.create_access_token(data = data)

        return {"Authorization": f"Bearer {access_token}"}

    def test_create_provider_service_requires_auth(self, client):
        response = client.post(
            "/provider-services/",
            json={
                "name": "Servicos de manicure",
                "service_id": "",
                "description": "Servicos de manicure Em Gel",
                "price": 1000,
            },
        )

        assert response.status_code == 401

    def test_create_provider_service_rejects_non_prestador(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(user)
        session.commit()

        headers = self._make_auth_header(user)

        response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "Servicos de manicure",
                "service_id": "",
                "description": "Servicos de manicure Em Gel",
                "price": 1000,
            },
        )

        assert response.status_code == 403

    def test_create_provider_service_by_name_success(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        headers = self._make_auth_header(provider)

        response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "Servicos de manicure",
                "service_id": "",
                "description": "Servicos de manicure Em Gel",
                "price": 1000,
            },
        )

        assert response.status_code == 201
        body = response.json()

        assert body["provider_id"] == str(provider.id)
        assert body["service_name"] == "servicos de manicure"
        assert body["description"] == "Servicos de manicure Em Gel"
        assert body["price"] == 1000

        assert session.query(ServiceModel).count() == 1
        assert session.query(ProviderServiceModel).count() == 1

    def test_create_provider_service_with_existing_service_id_success(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador 2",
            email="prestador2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        service = make_service(
            name="servicos de manicure",
            description="Servico existente",
        )

        session.add(
            ServiceModel(
                id=service.id,
                name=service.name,
                description=service.description,
            )
        )
        session.commit()

        headers = self._make_auth_header(provider)

        response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "",
                "service_id": str(service.id),
                "description": "Descricao ignorada nesse caso",
                "price": 1000,
            },
        )

        assert response.status_code == 201
        body = response.json()

        assert body["provider_id"] == str(provider.id)
        assert body["service_id"] == str(service.id)
        assert body["service_name"] == "servicos de manicure"

        assert session.query(ServiceModel).count() == 1
        assert session.query(ProviderServiceModel).count() == 1

    def test_create_provider_service_returns_409_when_already_exists(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador 3",
            email="prestador3@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        service = make_service(
            name="servicos de manicure",
            description="Servico existente",
        )

        session.add(
            ServiceModel(
                id=service.id,
                name=service.name,
                description=service.description,
            )
        )
        session.add(
            ProviderServiceModel(
                id=uuid4(),
                provider_id=provider.id,
                service_id=service.id,
                price=Decimal("1000.00"),
                active=True,
                created_at=None,
            )
        )
        session.commit()

        headers = self._make_auth_header(provider)

        response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": " SERVICOS DE MANICURE ",
                "service_id": "",
                "description": "Descricao qualquer",
                "price": 1000,
            },
        )

        assert response.status_code == 409
        body = response.json()
        assert "detail" in body

    def test_create_provider_service_returns_404_when_service_id_not_found(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador 4",
            email="prestador4@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        headers = self._make_auth_header(provider)

        response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "",
                "service_id": str(uuid4()),
                "description": "Descricao qualquer",
                "price": 1000,
            },
        )

        assert response.status_code == 404

    def test_create_provider_service_returns_422_when_name_and_service_id_are_invalid(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador 5",
            email="prestador5@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        headers = self._make_auth_header(provider)

        response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "",
                "service_id": "",
                "description": "Descricao qualquer",
                "price": 1000,
            },
        )

        assert response.status_code == 422
