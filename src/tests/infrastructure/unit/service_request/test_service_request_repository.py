from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from domain.service_request.service_request_exceptions import (
    ServiceRequestNotFoundError,
)
import pytest
from sqlalchemy.exc import IntegrityError

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestServiceRequestRepository:
    @staticmethod
    def _create_persisted_provider(session, make_user, is_active=True):
        repo = userRepository(session=session)
        provider = make_user(
            id=uuid4(),
            name=f"Prestador {uuid4()}",
            email=f"{uuid4()}@example.com",
            hashed_password="hashed_password",
            is_active=is_active,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        repo.add_user(provider)
        return provider

    @staticmethod
    def _create_persisted_client(session, make_user, is_active=True):
        repo = userRepository(session=session)
        provider = make_user(
            id=uuid4(),
            name=f"Prestador {uuid4()}",
            email=f"{uuid4()}@example.com",
            hashed_password="hashed_password",
            is_active=is_active,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        repo.add_user(provider)
        return provider

    @staticmethod
    def _create_persisted_service(
        session, service_id=None, name=None, description=None
    ):
        service = ServiceModel(
            id=service_id or uuid4(),
            name=name or f"Serviço {uuid4()}",
            description=description or "Descrição do serviço",
        )
        session.add(service)
        session.commit()
        return service

    def test_create_service_request(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Corte de cabelo",
            description="Corte masculino",
        )
        session.add(service)
        session.commit()

        entity = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua das Flores, 123",
        )

        created = repository.create(entity)

        assert created.id == entity.id
        assert created.client_id == client.id
        assert created.service_id == service.id
        assert created.status == ServiceRequestStatus.REQUESTED.value
        assert created.address == "Rua das Flores, 123"
        assert isinstance(created.created_at, datetime)

        persisted_model = (
            session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == entity.id)
            .first()
        )

        assert persisted_model is not None
        assert persisted_model.client_id == client.id
        assert persisted_model.service_id == service.id
        assert persisted_model.status == ServiceRequestStatus.REQUESTED.value

    def test_find_by_id_should_return_service_request(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente 2",
            email="cliente2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Manicure",
            description="Manicure simples",
        )
        session.add(service)
        session.commit()

        entity = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=2),
            address="Rua A, 100",
        )
        repository.create(entity)

        found = repository.find_by_id(entity.id)

        assert found is not None
        assert found.id == entity.id
        assert found.client_id == client.id
        assert found.service_id == service.id
        assert found.address == "Rua A, 100"

    def test_find_by_id_should_return_none_when_not_found(self, tst_db_session):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)

        found = repository.find_by_id(uuid4())

        assert found is None

    def test_list_by_client_id_should_return_service_requests_ordered_by_created_at_desc(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente 3",
            email="cliente3@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        other_client = make_user(
            id=uuid4(),
            name="Cliente 4",
            email="cliente4@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)
        user_repository.add_user(other_client)

        service = ServiceModel(
            id=uuid4(),
            name="Barba",
            description="Barba completa",
        )
        session.add(service)
        session.commit()

        older_request = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua 1",
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        newer_request = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=3),
            address="Rua 2",
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        other_client_request = ServiceRequest(
            id=uuid4(),
            client_id=other_client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=4),
            address="Rua 3",
        )

        repository.create(older_request)
        repository.create(newer_request)
        repository.create(other_client_request)

        result = repository.list_by_client_id(client.id)

        assert len(result) == 2
        assert result[0].id == newer_request.id
        assert result[1].id == older_request.id

    def test_list_by_client_id_should_return_empty_list_when_client_has_no_requests(
        self,
        tst_db_session,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)

        result = repository.list_by_client_id(uuid4())

        assert result == []

    def test_list_by_client_id_with_service_data(
        self, tst_db_session, make_user, make_service, seed_roles
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)

        # Create a user and services
        user = make_user()
        another_user = make_user()
        user_repository.add_user(user)
        user_repository.add_user(another_user)

        service1 = make_service(
            name="SERVIÇO DE ENTREGA DE CARTAS",
            description="SErViçO de Entrega de Cartas",
        )
        service2 = make_service(
            name="serviço de leitura de mãos",
            description="SErViçO de Leitura de Mãos",
        )
        service3 = make_service(name="Service 3", description="Description 3")

        service_repository.create_service(service1)
        service_repository.create_service(service2)
        service_repository.create_service(service3)

        # Create service requests
        service_request1 = ServiceRequest(
            id=uuid4(),
            client_id=user.id,
            service_id=service1.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua 1",
            created_at=datetime.utcnow(),
        )
        service_request2 = ServiceRequest(
            id=uuid4(),
            client_id=user.id,
            service_id=service2.id,
            desired_datetime=datetime.utcnow() + timedelta(days=2),
            address="Rua 2",
            created_at=datetime.utcnow(),
        )

        service_request3 = ServiceRequest(
            id=uuid4(),
            client_id=another_user.id,
            service_id=service3.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua 1",
            created_at=datetime.utcnow(),
        )
        repository.create(service_request1)
        repository.create(service_request2)
        repository.create(service_request3)

        # Call the method under test
        result = repository.list_by_client_id_with_service_data(user.id)

        # Assert that the result contains the correct service data in order the service requests were created (newest first)
        assert len(result) == 2
        assert (
            result[1].service_name == "Serviço de Entrega de Cartas"
        )  # Capitalize first letter and lowercase the rest
        assert (
            result[1].service_description == "SErViçO de Entrega de Cartas"
        )  # Not normalized
        assert result[1].client_id == user.id

        assert result[0].service_name == "Serviço de Leitura de Mãos"
        assert result[0].service_description == "SErViçO de Leitura de Mãos"
        assert result[0].client_id == user.id

    def test_create_should_persist_new_acceptance_fields(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente Persistencia",
            email="cliente.persistencia@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        provider = make_user(
            id=uuid4(),
            name="Prestador Persistencia",
            email="prestador.persistencia@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(client)
        user_repository.add_user(provider)

        service = ServiceModel(
            id=uuid4(),
            name="Massagem",
            description="Massagem relaxante",
        )
        session.add(service)
        session.commit()

        accepted_at = datetime.utcnow()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        entity = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            status=ServiceRequestStatus.CONFIRMED,
            address="Rua Principal, 10",
            accepted_provider_id=provider.id,
            departure_address="Rua do Prestador, 999",
            service_price=Decimal("150.00"),
            travel_price=Decimal("25.50"),
            total_price=Decimal("175.50"),
            accepted_at=accepted_at,
            expires_at=expires_at,
        )

        created = repository.create(entity)

        assert created.id == entity.id
        assert created.status == ServiceRequestStatus.CONFIRMED.value
        assert created.accepted_provider_id == provider.id
        assert created.departure_address == "Rua do Prestador, 999"
        assert created.service_price == Decimal("150.00")
        assert created.travel_price == Decimal("25.50")
        assert created.total_price == Decimal("175.50")
        assert created.accepted_at == accepted_at
        assert created.expires_at == expires_at

        persisted_model = (
            session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == entity.id)
            .first()
        )

        assert persisted_model is not None
        assert persisted_model.status == ServiceRequestStatus.CONFIRMED.value
        assert persisted_model.accepted_provider_id == provider.id
        assert persisted_model.departure_address == "Rua do Prestador, 999"
        assert persisted_model.service_price == Decimal("150.00")
        assert persisted_model.travel_price == Decimal("25.50")
        assert persisted_model.total_price == Decimal("175.50")
        assert persisted_model.accepted_at == accepted_at
        assert persisted_model.expires_at == expires_at

    def test_create_should_raise_error_when_accepted_provider_id_does_not_exist(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente FK",
            email="cliente.fk@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Serviço com FK",
            description="Teste de foreign key",
        )
        session.add(service)
        session.commit()

        request_id = uuid4()

        entity = ServiceRequest(
            id=request_id,
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            status=ServiceRequestStatus.CONFIRMED,
            address="Rua Teste, 123",
            accepted_provider_id=uuid4(),
            departure_address="Rua Origem, 999",
            service_price=Decimal("100.00"),
            travel_price=Decimal("20.00"),
            total_price=Decimal("120.00"),
            accepted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        with pytest.raises(IntegrityError):
            repository.create(entity)
            session.flush()

        session.rollback()

        persisted_model = (
            session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == request_id)
            .first()
        )

        assert persisted_model is None

    def test_find_by_id_should_hydrate_new_phase_1_fields(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente Hidratação",
            email="cliente.hidratacao@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        provider = make_user(
            id=uuid4(),
            name="Prestador Hidratação",
            email="prestador.hidratacao@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(client)
        user_repository.add_user(provider)

        service = ServiceModel(
            id=uuid4(),
            name="Consulta",
            description="Consulta presencial",
        )
        session.add(service)
        session.commit()

        accepted_at = datetime.utcnow()
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        entity = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=2),
            status=ServiceRequestStatus.CONFIRMED,
            address="Rua A, 100",
            accepted_provider_id=provider.id,
            departure_address="Rua B, 200",
            service_price=Decimal("89.90"),
            travel_price=Decimal("10.10"),
            total_price=Decimal("100.00"),
            accepted_at=accepted_at,
            expires_at=expires_at,
        )
        repository.create(entity)

        found = repository.find_by_id(entity.id)

        assert found is not None
        assert found.id == entity.id
        assert found.client_id == client.id
        assert found.service_id == service.id
        assert found.status == ServiceRequestStatus.CONFIRMED.value
        assert found.accepted_provider_id == provider.id
        assert found.departure_address == "Rua B, 200"
        assert found.service_price == Decimal("89.90")
        assert found.travel_price == Decimal("10.10")
        assert found.total_price == Decimal("100.00")
        assert found.accepted_at == accepted_at
        assert found.expires_at == expires_at

    def test_list_by_client_id_should_return_requests_with_null_prices_before_acceptance(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente Sem Aceite",
            email="cliente.sem.aceite@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Instalação",
            description="Instalação técnica",
        )
        session.add(service)
        session.commit()

        request = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE,
            address="Rua Sem Aceite, 50",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        repository.create(request)

        result = repository.list_by_client_id(client.id)

        assert len(result) == 1
        assert (
            result[0].status == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        )
        assert result[0].accepted_provider_id is None
        assert result[0].departure_address is None
        assert result[0].service_price is None
        assert result[0].travel_price is None
        assert result[0].total_price is None
        assert result[0].accepted_at is None
        assert result[0].expires_at is not None

    def test_list_by_client_id_should_return_prices_filled_after_confirmation(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente Confirmado",
            email="cliente.confirmado@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        provider = make_user(
            id=uuid4(),
            name="Prestador Confirmado",
            email="prestador.confirmado@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(client)
        user_repository.add_user(provider)

        service = ServiceModel(
            id=uuid4(),
            name="Visita Técnica",
            description="Visita técnica residencial",
        )
        session.add(service)
        session.commit()

        accepted_at = datetime.utcnow()

        confirmed_request = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=3),
            status=ServiceRequestStatus.CONFIRMED,
            address="Rua Confirmada, 77",
            accepted_provider_id=provider.id,
            departure_address="Rua Origem, 12",
            service_price=Decimal("200.00"),
            travel_price=Decimal("35.00"),
            total_price=Decimal("235.00"),
            accepted_at=accepted_at,
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        repository.create(confirmed_request)

        result = repository.list_by_client_id(client.id)

        assert len(result) == 1
        assert result[0].status == ServiceRequestStatus.CONFIRMED.value
        assert result[0].accepted_provider_id == provider.id
        assert result[0].departure_address == "Rua Origem, 12"
        assert result[0].service_price == Decimal("200.00")
        assert result[0].travel_price == Decimal("35.00")
        assert result[0].total_price == Decimal("235.00")
        assert result[0].accepted_at == accepted_at

    def test_update_service_request_should_update_existing_request(
        self, tst_db_session, make_user, make_service
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente 1",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Corte de cabelo",
            description="Corte masculino",
        )
        session.add(service)
        session.commit()

        entity = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua das Flores, 123",
        )

        created = repository.create(entity)

        # Update the service request
        entity.address = "Rua das Flores, 456"
        timeexpire = datetime.utcnow() + timedelta(hours=1)
        entity.status = ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        entity.expires_at = timeexpire
        updated = repository.update(entity)

        assert updated.id == created.id
        assert updated.address == "Rua das Flores, 456"
        assert updated.status == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        assert updated.expires_at == timeexpire

        persisted_model = (
            session.query(ServiceRequestModel)
            .filter(ServiceRequestModel.id == created.id)
            .first()
        )
        assert persisted_model is not None
        assert persisted_model.address == "Rua das Flores, 456"
        assert (
            persisted_model.status
            == ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value
        )
        assert persisted_model.expires_at == timeexpire

    def test_update_service_request_should_raise_not_found_error(self, tst_db_session):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)

        non_existent_request = ServiceRequest(
            id=uuid4(),
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua Inexistente, 123",
        )

        with pytest.raises(ServiceRequestNotFoundError):
            repository.update(non_existent_request)

    def test_list_available_for_provider_should_return_available_service_requests(
        self,
        tst_db_session,
        make_user,
        make_service,
        make_provider_service,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        Prov_serv = ProviderServiceRepository(session=session)

        provider = self._create_persisted_provider(session, make_user)
        client = self._create_persisted_client(session, make_user)
        service = self._create_persisted_service(
            session,
            name="Serviço 1",
            description="Descrição 1",
        )

        provider_service = make_provider_service(
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )
        Prov_serv.create_provider_service(provider_service)
        session.commit()

        service_request = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="123 Main St",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        repository.create(service_request)

        result = repository.list_available_for_provider(provider.id)

        assert len(result) == 1
        assert result[0].service_request_id == service_request.id
        assert result[0].client_id == client.id
        assert result[0].service_id == service.id
        assert result[0].provider_service_id == provider_service.id
        assert result[0].price == provider_service.price

    def test_list_available_for_provider_should_return_empty_when_no_requests_available(
        self,
        tst_db_session,
        make_user,
        make_service,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Provider 2",
            email="provider2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )

        result = repository.list_available_for_provider(provider.id)

        assert result == []

    def test_list_available_for_provider_should_return_available_service_requests_order(
        self,
        tst_db_session,
        make_user,
        make_service,
        make_provider_service,
        seed_roles,
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        Prov_serv = ProviderServiceRepository(session=session)

        provider = self._create_persisted_provider(session, make_user)
        client1 = self._create_persisted_client(session, make_user)
        client2 = self._create_persisted_client(session, make_user)

        service = self._create_persisted_service(
            session,
            name="Serviço 1",
            description="Descrição 1",
        )

        provider_service = make_provider_service(
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )
        Prov_serv.create_provider_service(provider_service)
        session.commit()

        service_request1 = ServiceRequest(
            id=uuid4(),
            client_id=client1.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="123 Main St",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        repository.create(service_request1)

        service_request2 = ServiceRequest(
            id=uuid4(),
            client_id=client2.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="456 Main St",
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        repository.create(service_request2)

        result = repository.list_available_for_provider(provider.id)

        assert len(result) == 2
        assert result[0].service_request_id == service_request1.id
        assert result[0].client_id == client1.id
        assert result[0].service_id == service.id
        assert result[0].provider_service_id == provider_service.id
        assert result[0].price == provider_service.price

        assert result[1].service_request_id == service_request2.id
        assert result[1].client_id == client2.id
        assert result[1].service_id == service.id
        assert result[1].provider_service_id == provider_service.id
        assert result[1].price == provider_service.price

    def test_list_operational_schedule_for_provider(self, tst_db_session, make_user):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Provider 1",
            email="provider1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        client = make_user(
            id=uuid4(),
            name="Client 1",
            email="client1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Service 1",
            description="Description of Service 1",
        )
        session.add(service)
        session.commit()
        accepted_at = datetime.utcnow()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        confirmed_request = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Address 1",
            status=ServiceRequestStatus.CONFIRMED.value,
            accepted_provider_id=provider.id,
            departure_address="Rua do Prestador, 999",
            service_price=Decimal("150.00"),
            travel_price=Decimal("25.50"),
            total_price=Decimal("175.50"),
            accepted_at=accepted_at,
            expires_at=expires_at,
        )
        repository.create(confirmed_request)
        session.commit()

        result = repository.list_operational_schedule_for_provider(provider.id)

        assert len(result) == 1
        assert result[0].service_request_id == confirmed_request.id
        assert result[0].provider_id == provider.id
        assert result[0].client_id == client.id
        assert result[0].service_id == service.id
        assert result[0].desired_datetime == confirmed_request.desired_datetime

    def test_list_operational_schedule_for_provider_with_date_range(
        self, tst_db_session, make_user
    ):
        session = tst_db_session
        repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Provider 2",
            email="provider2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        client = make_user(
            id=uuid4(),
            name="Client 2",
            email="client2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Service 2",
            description="Description of Service 2",
        )
        session.add(service)
        session.commit()
        accepted_at = datetime.utcnow()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        confirmed_request_within_range = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Address 2",
            status=ServiceRequestStatus.CONFIRMED.value,
            accepted_provider_id=provider.id,
            departure_address="Rua do Prestador, 999",
            service_price=Decimal("150.00"),
            travel_price=Decimal("25.50"),
            total_price=Decimal("175.50"),
            accepted_at=accepted_at,
            expires_at=expires_at,
        )
        repository.create(confirmed_request_within_range)

        accepted_at = datetime.utcnow()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        confirmed_request_outside_range = ServiceRequest(
            id=uuid4(),
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=10),
            address="Address 3",
            status=ServiceRequestStatus.CONFIRMED.value,
            accepted_provider_id=provider.id,
            departure_address="Rua do Prestador, 999",
            service_price=Decimal("150.00"),
            travel_price=Decimal("25.50"),
            total_price=Decimal("175.50"),
            accepted_at=accepted_at,
            expires_at=expires_at,
        )
        repository.create(confirmed_request_outside_range)

        start_date = datetime.utcnow()
        end_date = datetime.utcnow() + timedelta(days=5)

        result = repository.list_operational_schedule_for_provider(
            provider.id, start=start_date, end=end_date
        )

        assert len(result) == 1
        assert result[0].service_request_id == confirmed_request_within_range.id
