from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_dto import (
    ListAvailableServiceRequestsForProviderInputDTO,
)
from usecases.service_request.list_available_service_requests_for_provider.list_available_service_requests_for_provider_usecase import (
    ListAvailableServiceRequestsForProviderUseCase,
)


class TestListAvailableServiceRequestsForProviderUseCase:
    @staticmethod
    def _create_provider(user_repository, make_user, *, name, email, is_active=True):
        provider = make_user(
            id=uuid4(),
            name=name,
            email=email,
            hashed_password="hashed_password",
            is_active=is_active,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        return provider

    @staticmethod
    def _create_client(user_repository, make_user, *, name, email, is_active=True):
        client = make_user(
            id=uuid4(),
            name=name,
            email=email,
            hashed_password="hashed_password",
            is_active=is_active,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)
        return client

    @staticmethod
    def _create_service(service_repository, make_service, *, name, description):
        service = make_service(
            id=uuid4(),
            name=name,
            description=description,
        )
        service_repository.create_service(service)
        return service

    @staticmethod
    def _create_provider_service(
        provider_service_repository,
        make_provider_service,
        *,
        provider_id,
        service_id,
        price=Decimal("100.00"),
        active=True,
    ):
        provider_service = make_provider_service(
            provider_id=provider_id,
            service_id=service_id,
            price=price,
            active=active,
        )
        provider_service_repository.create_provider_service(provider_service)
        return provider_service

    @staticmethod
    def _create_service_request(
        service_request_repository,
        *,
        client_id,
        service_id,
        status,
        expires_at,
        desired_datetime=None,
        address="Rua Teste, 123",
        created_at=None,
        accepted_provider_id=None,
        departure_address=None,
        service_price=None,
        travel_price=None,
        total_price=None,
        accepted_at=None,
    ):
        service_request = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=desired_datetime or (datetime.utcnow() + timedelta(days=1)),
            address=address,
            status=status,
            created_at=created_at or datetime.utcnow(),
            expires_at=expires_at,
            accepted_provider_id=accepted_provider_id,
            departure_address=departure_address,
            service_price=service_price,
            travel_price=travel_price,
            total_price=total_price,
            accepted_at=accepted_at,
        )
        service_request_repository.create(service_request)
        return service_request

    def test_list_available_includes_awaiting_with_future_expiry(
        self,
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

        provider = self._create_provider(
            user_repository,
            make_user,
            name="Prestador 1",
            email="prestador1@example.com",
        )
        client = self._create_client(
            user_repository,
            make_user,
            name="Cliente 1",
            email="cliente1@example.com",
        )
        service = self._create_service(
            service_repository,
            make_service,
            name="manicure em gel",
            description="Serviço de manicure em gel",
        )
        provider_service = self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("150.00"),
            active=True,
        )

        session.commit()

        service_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=2),
        )

        session.commit()

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
        )

        output = use_case.execute(
            ListAvailableServiceRequestsForProviderInputDTO(provider_id=provider.id)
        )

        assert len(output) == 1
        assert output[0].service_request_id == service_request.id
        assert output[0].client_id == client.id
        assert output[0].service_id == service.id
        assert output[0].provider_service_id == provider_service.id
        assert output[0].price == Decimal("150.00")
        assert output[0].status == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value

    def test_list_available_excludes_expired_requests(
        self,
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

        provider = self._create_provider(
            user_repository,
            make_user,
            name="Prestador 1",
            email="prestador1@example.com",
        )
        client = self._create_client(
            user_repository,
            make_user,
            name="Cliente 1",
            email="cliente1@example.com",
        )
        service = self._create_service(
            service_repository,
            make_service,
            name="Limpeza residencial",
            description="Serviço de limpeza",
        )
        self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider.id,
            service_id=service.id,
            active=True,
        )

        session.commit()

        expired_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        valid_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )

        session.commit()

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
        )

        output = use_case.execute(
            ListAvailableServiceRequestsForProviderInputDTO(provider_id=provider.id)
        )

        returned_ids = {item.service_request_id for item in output}

        assert valid_request.id in returned_ids
        assert expired_request.id not in returned_ids
        assert len(output) == 1

    def test_list_available_excludes_other_statuses(
        self,
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

        provider = self._create_provider(
            user_repository,
            make_user,
            name="Prestador 1",
            email="prestador1@example.com",
        )
        client = self._create_client(
            user_repository,
            make_user,
            name="Cliente 1",
            email="cliente1@example.com",
        )
        service = self._create_service(
            service_repository,
            make_service,
            name="Massagem relaxante",
            description="Serviço de massagem",
        )
        self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider.id,
            service_id=service.id,
            active=True,
        )

        session.commit()

        valid_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        requested_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service.id,
            status="REQUESTED",
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        confirmed_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.CONFIRMED.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
            accepted_provider_id=provider.id,
            departure_address="Rua de saída, 456",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=datetime.utcnow(),
        )

        session.commit()

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
        )

        output = use_case.execute(
            ListAvailableServiceRequestsForProviderInputDTO(provider_id=provider.id)
        )

        returned_ids = {item.service_request_id for item in output}

        assert valid_request.id in returned_ids
        assert requested_request.id not in returned_ids
        assert confirmed_request.id not in returned_ids
        assert len(output) == 1

    def test_list_available_excludes_inactive_provider_service(
        self,
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

        provider = self._create_provider(
            user_repository,
            make_user,
            name="Prestador 1",
            email="prestador1@example.com",
        )
        client = self._create_client(
            user_repository,
            make_user,
            name="Cliente 1",
            email="cliente1@example.com",
        )

        active_service = self._create_service(
            service_repository,
            make_service,
            name="Hidratação capilar",
            description="Serviço ativo",
        )
        inactive_service = self._create_service(
            service_repository,
            make_service,
            name="Escova progressiva",
            description="Serviço inativo",
        )

        self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider.id,
            service_id=active_service.id,
            active=True,
        )
        self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider.id,
            service_id=inactive_service.id,
            active=False,
        )

        session.commit()

        active_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=active_service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        inactive_request = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=inactive_service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )

        session.commit()

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
        )

        output = use_case.execute(
            ListAvailableServiceRequestsForProviderInputDTO(provider_id=provider.id)
        )

        returned_ids = {item.service_request_id for item in output}

        assert active_request.id in returned_ids
        assert inactive_request.id not in returned_ids
        assert len(output) == 1

    def test_list_available_excludes_requests_for_other_providers(
        self,
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

        provider_1 = self._create_provider(
            user_repository,
            make_user,
            name="Prestador 1",
            email="prestador1@example.com",
        )
        provider_2 = self._create_provider(
            user_repository,
            make_user,
            name="Prestador 2",
            email="prestador2@example.com",
        )
        client = self._create_client(
            user_repository,
            make_user,
            name="Cliente 1",
            email="cliente1@example.com",
        )

        service_provider_1 = self._create_service(
            service_repository,
            make_service,
            name="Barba",
            description="Serviço do prestador 1",
        )
        service_provider_2 = self._create_service(
            service_repository,
            make_service,
            name="Sobrancelha",
            description="Serviço do prestador 2",
        )

        self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider_1.id,
            service_id=service_provider_1.id,
            active=True,
        )
        self._create_provider_service(
            provider_service_repository,
            make_provider_service,
            provider_id=provider_2.id,
            service_id=service_provider_2.id,
            active=True,
        )

        session.commit()

        request_for_provider_1 = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service_provider_1.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        request_for_provider_2 = self._create_service_request(
            service_request_repository,
            client_id=client.id,
            service_id=service_provider_2.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )

        session.commit()

        use_case = ListAvailableServiceRequestsForProviderUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
        )

        output = use_case.execute(
            ListAvailableServiceRequestsForProviderInputDTO(provider_id=provider_1.id)
        )

        returned_ids = {item.service_request_id for item in output}

        assert request_for_provider_1.id in returned_ids
        assert request_for_provider_2.id not in returned_ids
        assert len(output) == 1