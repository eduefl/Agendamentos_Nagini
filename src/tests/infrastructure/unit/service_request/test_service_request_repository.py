from datetime import datetime, timedelta
from uuid import uuid4

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestServiceRequestRepository:
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
