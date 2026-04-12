from unittest.mock import patch
from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestListServicesRoute:
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

    def test_list_services_requires_auth(self, client):
        response = client.get("/services/")

        assert response.status_code == 401

    def test_list_services_success_for_authenticated_cliente(
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

        session.add_all(
            [
                ServiceModel(
                    id=uuid4(),
                    name="banho e tosa",
                    description="Serviço para pets",
                ),
                ServiceModel(
                    id=uuid4(),
                    name="limpeza residencial",
                    description="Serviço de limpeza completa",
                ),
            ]
        )
        session.commit()

        headers = self._make_auth_header(user)

        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 2

        service_names = {item["name"] for item in body}
        expected_names = {"Banho e Tosa", "Limpeza Residencial"}
        assert service_names == expected_names

    def test_list_services_success_for_authenticated_prestador(
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
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)

        service_1_id = uuid4()
        service_2_id = uuid4()

        session.add_all(
            [
                ServiceModel(
                    id=service_1_id,
                    name="manicure",
                    description="Serviço de manicure",
                ),
                ServiceModel(
                    id=service_2_id,
                    name="pedicure",
                    description="Serviço de pedicure",
                ),
            ]
        )
        session.commit()

        headers = self._make_auth_header(user)

        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 2

        returned_ids = {item["service_id"] for item in body}
        assert returned_ids == {str(service_1_id), str(service_2_id)}

        returned_names = {item["name"] for item in body}
        assert returned_names == {"Manicure", "Pedicure"}

    def test_list_services_returns_empty_list_when_there_are_no_services(
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
            name="Usuário 1",
            email="usuario1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(user)
        session.commit()

        headers = self._make_auth_header(user)

        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert body == []

    def test_list_services_returns_sorted_list_of_services(
        self,
        client,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Usuário 1",
            email="usuario1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)
        session.commit()

        # Add services with different names
        
        service1 = make_service(name="Service A")
        service2 = make_service(name="Service B")
        service3 = make_service(name="Service C")

        # Convert domain entities to ORM models
        service1_db = ServiceModel(id=service1.id, name=service1.name, description=service1.description)
        service2_db = ServiceModel(id=service2.id, name=service2.name, description=service2.description)
        service3_db = ServiceModel(id=service3.id, name=service3.name, description=service3.description)

        session.add_all([service1_db, service2_db, service3_db])
        session.commit()

        headers = self._make_auth_header(user)

        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert isinstance(body, list)
        assert len(body) == 3
        assert body[0]["name"] == "Service A"
        assert body[1]["name"] == "Service B"
        assert body[2]["name"] == "Service C"

    def test_list_services_handles_multiple_spaces(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Usuário 2",
            email="usuario2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)
        session.commit()

        service = make_service(name="    Service    A    ")  # Multiple spaces
        service1_db = ServiceModel(id=service.id, name=service.name, description=service.description)

        session.add(service1_db)
        session.commit()

        headers = self._make_auth_header(user)
        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"].strip() == "Service A"

    

    def test_list_services_handles_capitalized_names(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Usuário 4",
            email="usuario4@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)
        session.commit()

        service = make_service(name="Service A")  # Already capitalized
        service_db = ServiceModel(id=service.id, name=service.name, description=service.description)
        session.add(service_db)
        session.commit()

        headers = self._make_auth_header(user)
        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"] == "Service A"

    def test_list_services_handles_connectors(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Usuário 5",
            email="usuario5@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)
        session.commit()

        service1 = make_service(name="1 - SERVIÇO DE LIMPEZA")
        service2 = make_service(name="2 - SERVIÇO DA LIMPEZA")
        service3 = make_service(name="3 - SERVIÇO DO LIMPEZA")
        service4 = make_service(name="4 - SERVIÇO E LIMPEZA")

        # Convert domain entities to ORM models
        service1_db = ServiceModel(id=service1.id, name=service1.name, description=service1.description)
        service2_db = ServiceModel(id=service2.id, name=service2.name, description=service2.description)
        service3_db = ServiceModel(id=service3.id, name=service3.name, description=service3.description)
        service4_db = ServiceModel(id=service4.id, name=service4.name, description=service4.description)


        session.add_all([service1_db, service2_db, service3_db,service4_db])
        session.commit()


        headers = self._make_auth_header(user)
        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 4
        assert body[0]["name"] == "1 - Serviço de Limpeza"
        assert body[1]["name"] == "2 - Serviço da Limpeza"
        assert body[2]["name"] == "3 - Serviço do Limpeza"
        assert body[3]["name"] == "4 - Serviço e Limpeza"

    def test_list_services_handles_accents_and_compound_terms(
        self, client, tst_db_session, make_user, make_service, seed_roles
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Usuário 6",
            email="usuario6@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)
        session.commit()

        service = make_service(
            name="Serviço de Jardinagem"
        )  # Compound term with accent
        service_db = ServiceModel(id=service.id, name=service.name, description=service.description)
        session.add(service_db)
        session.commit()

        headers = self._make_auth_header(user)
        response = client.get("/services/", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"] == "Serviço de Jardinagem"


    def test_list_services_returns_500_when_usecase_raises_unexpected_error(
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
            email="client.error@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(user)
        session.commit()

        headers = self._make_auth_header(user)

        with patch(
            "infrastructure.api.routers.service_routers.make_list_services_usecase",
            side_effect=RuntimeError("unexpected error"),
        ):
            response = client.get("/services/", headers=headers)

        assert response.status_code == 500