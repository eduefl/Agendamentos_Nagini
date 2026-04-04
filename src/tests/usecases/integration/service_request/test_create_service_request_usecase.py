from datetime import datetime, timedelta
from uuid import uuid4

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service.service_exceptions import ServiceNotFoundError
from domain.service_request.service_request_exceptions import (
    InvalidServiceRequestDateError,
)
from domain.user.user_exceptions import UserNotFoundError
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.create_service_request.create_service_request_dto import (
    CreateServiceRequestInputDTO,
    CreateServiceRequestOutputDTO,
)
from usecases.service_request.create_service_request.create_service_request_usecase import (
    CreateServiceRequestUseCase,
)


class TestCreateServiceRequestUseCaseIntegration:
    def test_create_service_request_success(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente",
            email="cliente@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Depilação",
            description="Serviço de depilação",
        )
        session.add(service)
        session.commit()

        use_case = CreateServiceRequestUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="Rua das Acácias, 45",
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, CreateServiceRequestOutputDTO)
        assert output.client_id == client.id
        assert output.service_id == service.id
        assert output.status == "AWAITING_PROVIDER_ACCEPTANCE"
        assert output.address == "Rua das Acácias, 45"

        persisted = service_request_repository.find_by_id(output.service_request_id)
        assert persisted is not None
        assert persisted.client_id == client.id
        assert persisted.service_id == service.id
        assert persisted.status == "AWAITING_PROVIDER_ACCEPTANCE"

    def test_create_service_request_user_not_found(
        self,
        tst_db_session,
    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)

        use_case = CreateServiceRequestUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=uuid4(),
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

    def test_create_service_request_client_inactive(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)

        client = make_user(
            id=uuid4(),
            name="Cliente Inativo",
            email="cliente_inativo@example.com",
            hashed_password="hashed_password",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client)
        session.commit()

        use_case = CreateServiceRequestUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client.id,
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_create_service_request_user_not_client(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Prestador",
            email="prestador@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(user)
        session.commit()

        use_case = CreateServiceRequestUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=user.id,
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_create_service_request_service_not_found(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)

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
        session.commit()

        use_case = CreateServiceRequestUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client.id,
            service_id=uuid4(),
            desired_datetime=datetime.utcnow() + timedelta(days=1),
        )

        with pytest.raises(ServiceNotFoundError):
            use_case.execute(input_dto)

    def test_create_service_request_should_raise_error_when_desired_datetime_is_in_past(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)

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
        user_repository.add_user(client)

        service = ServiceModel(
            id=uuid4(),
            name="Massagem",
            description="Massagem relaxante",
        )
        session.add(service)
        session.commit()

        use_case = CreateServiceRequestUseCase(
            service_request_repository=service_request_repository,
            user_repository=user_repository,
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
        )

        input_dto = CreateServiceRequestInputDTO(
            client_id=client.id,
            service_id=service.id,
            desired_datetime=datetime.utcnow() - timedelta(minutes=1),
        )

        with pytest.raises(InvalidServiceRequestDateError):
            use_case.execute(input_dto)
