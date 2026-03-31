from uuid import uuid4

from domain.security.token_service_dto import CreateAccessTokenDTO
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestActivateProviderServiceRoute:
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

    def test_activate_provider_service_requires_auth(self, client):
        response = client.patch(f"/provider-services/{uuid4()}/activate")
        assert response.status_code == 401

    def test_activate_provider_service_rejects_non_prestador(
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
        session.commit()

        headers = self._make_auth_header(client_user)

        response = client.patch(
            f"/provider-services/{uuid4()}/activate",
            headers=headers,
        )

        assert response.status_code == 403

    def test_activate_provider_service_success(
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

        create_response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "Servicos de manicure",
                "service_id": "",
                "description": "Servicos de manicure em gel",
                "price": 1000,
            },
        )

        assert create_response.status_code == 201
        created_body = create_response.json()
        provider_service_id = created_body["provider_service_id"]

        deactivate_response = client.patch(
            f"/provider-services/{provider_service_id}/deactivate",
            headers=headers,
        )
        assert deactivate_response.status_code == 200

        response = client.patch(
            f"/provider-services/{provider_service_id}/activate",
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()

        assert body["provider_service_id"] == provider_service_id
        assert body["provider_id"] == str(provider.id)
        assert body["active"] is True

    def test_activate_provider_service_returns_404_when_not_found(
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
            name="Prestador 2",
            email="prestador2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        headers = self._make_auth_header(provider)

        response = client.patch(
            f"/provider-services/{uuid4()}/activate",
            headers=headers,
        )

        assert response.status_code == 404
        body = response.json()
        assert body["detail"] == "Provider service not found"

    def test_activate_provider_service_rejects_service_from_another_provider(
        self,
        client,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider_a = make_user(
            id=uuid4(),
            name="Prestador A",
            email="prestador_a@example.com",
            hashed_password="hashed_password_a",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        provider_b = make_user(
            id=uuid4(),
            name="Prestador B",
            email="prestador_b@example.com",
            hashed_password="hashed_password_b",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )

        user_repository.add_user(provider_a)
        user_repository.add_user(provider_b)
        session.commit()

        headers_b = self._make_auth_header(provider_b)

        create_response = client.post(
            "/provider-services/",
            headers=headers_b,
            json={
                "name": "Servico do prestador B",
                "service_id": "",
                "description": "Descricao do servico do prestador B",
                "price": 1500,
            },
        )

        assert create_response.status_code == 201
        created_body = create_response.json()
        provider_service_id = created_body["provider_service_id"]

        client.patch(
            f"/provider-services/{provider_service_id}/deactivate",
            headers=headers_b,
        )

        headers_a = self._make_auth_header(provider_a)

        response = client.patch(
            f"/provider-services/{provider_service_id}/activate",
            headers=headers_a,
        )

        assert response.status_code == 403
        body = response.json()
        assert body["detail"] == "Apenas o prestador dono do serviço pode ativá-lo"

    def test_activate_provider_service_returns_409_when_already_active(
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
            name="Prestador 3",
            email="prestador3@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        headers = self._make_auth_header(provider)

        create_response = client.post(
            "/provider-services/",
            headers=headers,
            json={
                "name": "Servico ja ativo",
                "service_id": "",
                "description": "Descricao do servico",
                "price": 2000,
            },
        )

        assert create_response.status_code == 201
        created_body = create_response.json()
        provider_service_id = created_body["provider_service_id"]

        response = client.patch(
            f"/provider-services/{provider_service_id}/activate",
            headers=headers,
        )

        assert response.status_code == 409
        body = response.json()
        assert body["detail"] == "This provider service is already active"
