from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.service_request.service_request_entity import ServiceRequestStatus
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)


class TestAcceptServiceRequestNotificationRoute:
    def _make_auth_header(self, user):
        token_service = make_token_service()
        roles = [
            role.name if hasattr(role, "name") else str(role) for role in user.roles
        ]
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

    def _create_available_service_request(
        self, session, client_id, service_id, provider_id, provider_price
    ):
        service_model = (
            session.query(ServiceModel).filter(ServiceModel.id == service_id).first()
        )
        assert service_model is not None

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

    def test_accept_still_returns_200_and_sends_notifications(
        self, client, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        sr = self._create_available_service_request(
            session,
            client_user.id,
            service.id,
            provider_id=provider.id,
            provider_price=Decimal("100.00"),
        )

        fake_sender = MagicMock()

        with patch(
            "infrastructure.api.factories.make_confirm_service_request_usecase.SMTPEmailSender",
            return_value=fake_sender,
        ):
            headers = self._make_auth_header(provider)
            response = client.patch(
                f"/provider-service-requests/{sr.id}/accept",
                headers=headers,
                json={"departure_address": "Rua Saída, 123"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ServiceRequestStatus.CONFIRMED.value

        fake_sender.send_service_request_confirmed_to_client.assert_called_once()
        fake_sender.send_service_request_confirmed_to_provider.assert_called_once()

        client_call_kwargs = (
            fake_sender.send_service_request_confirmed_to_client.call_args.kwargs
        )
        assert float(client_call_kwargs["service_price"]) == 100.0
        assert client_call_kwargs["status"] == ServiceRequestStatus.CONFIRMED.value

        provider_call_kwargs = (
            fake_sender.send_service_request_confirmed_to_provider.call_args.kwargs
        )
        assert float(provider_call_kwargs["service_price"]) == 100.0
        assert provider_call_kwargs["service_address"] == "Rua Destino, 100"

    def test_accept_remains_confirmed_even_if_smtp_raises(
        self, client, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        client_user = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})

        service = ServiceModel(id=uuid4(), name=f"srv {uuid4().hex}", description="D")
        session.add(service)
        session.commit()

        sr = self._create_available_service_request(
            session,
            client_user.id,
            service.id,
            provider_id=provider.id,
            provider_price=Decimal("100.00"),
        )

        failing_sender = MagicMock()
        failing_sender.send_service_request_confirmed_to_client.side_effect = Exception(
            "SMTP error"
        )
        failing_sender.send_service_request_confirmed_to_provider.side_effect = (
            Exception("SMTP error")
        )

        with patch(
            "infrastructure.api.factories.make_confirm_service_request_usecase.SMTPEmailSender",
            return_value=failing_sender,
        ):
            headers = self._make_auth_header(provider)
            response = client.patch(
                f"/provider-service-requests/{sr.id}/accept",
                headers=headers,
                json={"departure_address": "Rua Saída, 1"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ServiceRequestStatus.CONFIRMED.value
