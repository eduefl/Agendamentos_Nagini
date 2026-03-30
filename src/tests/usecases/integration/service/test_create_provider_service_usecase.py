from domain.__seedwork.exceptions import ForbiddenError

from pydantic import ValidationError

import pytest
from decimal import Decimal
from uuid import uuid4

from domain.service.service_exceptions import (
    ProviderServiceAlreadyExistsError,
    ServiceNotFoundError,
)
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.create_provider_service.create_provider_service_dto import (
    CreateProviderServiceInputDTO,
)
from usecases.service.create_provider_service.create_provider_service_usecase import (
    CreateProviderServiceUseCase,
)


class TestCreateProviderServiceIntegration:
    def test_execute_creates_service_and_provider_service(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            name="Service 1",
            description="Description for Service 1",
            price=Decimal("100.00"),
        )

        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )

        output_dto = use_case.execute(input_dto)

        assert output_dto.provider_id == provider_id
        assert output_dto.service_name == "service 1"
        assert output_dto.description == "Description for Service 1"
        assert output_dto.price == Decimal("100.00")

        assert session.query(ServiceModel).count() == 1
        assert session.query(ProviderServiceModel).count() == 1

    def test_execute_raises_error_if_provider_service_exists(
        self,
        tst_db_session,
        make_service,
        make_provider_service,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        existing_service = make_service()

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 2",
            email="prestador2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        service_id = existing_service.id
        service_name = existing_service.name

        service_repository.create_service(existing_service)

        existing_provider_service = make_provider_service(
            provider_id=provider_id,
            service_id=service_id,
        )
        provider_service_repository.create_provider_service(existing_provider_service)
        session.commit()

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            name=service_name,
            description="Description for Service 1",
            price=Decimal("100.00"),
        )

        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )

        with pytest.raises(ProviderServiceAlreadyExistsError):
            use_case.execute(input_dto)

    def test_execute_rolls_back_on_exception(
        self,
        tst_db_session,
        make_service,
        make_provider_service,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        existing_service = make_service()

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 3",
            email="prestador3@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        service_id = existing_service.id
        service_name = existing_service.name

        service_repository.create_service(existing_service)

        existing_provider_service = make_provider_service(
            provider_id=provider_id,
            service_id=service_id,
        )
        provider_service_repository.create_provider_service(existing_provider_service)
        session.commit()

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            name=service_name,
            description="Description for Service 1",
            price=Decimal("100.00"),
        )

        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )

        with pytest.raises(ProviderServiceAlreadyExistsError):
            use_case.execute(input_dto)

        results = provider_service_repository.list_by_provider_id(provider_id)
        assert len(results) == 1
        assert service_repository.find_by_name(service_name) is not None

    def test_execute_creates_provider_service_only_if_service_exists(
        self,
        tst_db_session,
        make_service,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        existing_service = make_service()

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 4",
            email="prestador4@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        service_name = existing_service.name

        service_repository.create_service(existing_service)
        session.commit()

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            name=service_name,
            description="Description for Service 1",
            price=Decimal("100.00"),
        )

        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )

        output_dto = use_case.execute(input_dto)

        assert output_dto.provider_id == provider_id
        assert output_dto.service_name == service_name.strip().lower()
        assert session.query(ServiceModel).count() == 1
        assert session.query(ProviderServiceModel).count() == 1

    def test_execute_raises_forbidden_if_user_is_not_prestador(
        self,
        tst_db_session,
        make_service,
        make_user,
        seed_roles,
    ):

        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        existing_service = make_service()

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 4",
            email="prestador4@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(provider)

        service_name = existing_service.name

        service_repository.create_service(existing_service)
        session.commit()

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            name=service_name,
            description="Description for Service 1",
            price=Decimal("100.00"),
        )

        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )
        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_execute_does_not_create_duplicate_service(
        self,
        tst_db_session,
        make_service,
        make_user,
        seed_roles,
        make_provider_service,
    ):

        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        existing_service = make_service(name="service 1")
        service_repository.create_service(existing_service)
        session.commit()
        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            name=" SERVICE 1 ",
            description="Description for Service 1",
            price=Decimal("100.00"),
        )
        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )
        output_dto = use_case.execute(input_dto)
        assert output_dto.provider_id == provider_id
        assert output_dto.service_name == "service 1"
        assert output_dto.price == Decimal("100.00")
        assert session.query(ServiceModel).count() == 1

    # validate when service_id is filled and service exist, should create provider service with that service_id
    def test_execute_creates_provider_service_with_existing_service_id(
        self,
        tst_db_session,
        make_service,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        service_repository = ServiceRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        existing_service = make_service(name="service 1")
        service_repository.create_service(existing_service)
        session.commit()

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            description="Description for Service 1",
            price=Decimal("100.00"),
            service_id=existing_service.id,  # Assuming service_id is part of the DTO
        )
        use_case = CreateProviderServiceUseCase(
            service_repository=service_repository,
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
            session=session,
        )
        output_dto = use_case.execute(input_dto)
        assert output_dto.provider_id == provider_id
        assert output_dto.service_name == "service 1"
        assert output_dto.price == Decimal("100.00")
        assert session.query(ServiceModel).count() == 1
        assert session.query(ProviderServiceModel).count() == 1

    # validate when service_id is filled but service does not exist, should raise ServiceNotFoundError
    def test_execute_raises_service_not_found_error_if_service_does_not_exist(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        input_dto = CreateProviderServiceInputDTO(
            provider_id=provider_id,
            description="Description for Non-existent Service",
            price=Decimal("100.00"),
            service_id=uuid4(),  # Non-existent service_id
        )
        use_case = CreateProviderServiceUseCase(
            service_repository=ServiceRepository(session=session),
            provider_service_repository=ProviderServiceRepository(session=session),
            user_repository=user_repository,
            session=session,
        )

        with pytest.raises(ServiceNotFoundError):
            use_case.execute(input_dto)

    # validate when name is empty and service_id is empty or when both are filled, should raise ValueError
    def test_execute_raises_value_error_if_name_and_service_id_are_empty_or_both_filled(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        user_repository = userRepository(session=session)

        provider_id = uuid4()
        provider = make_user(
            id=provider_id,
            name="Prestador 1",
            email="prestador1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)

        # Test case 1: Both name and service_id are empty
        with pytest.raises(ValidationError):
            CreateProviderServiceInputDTO(
                provider_id=provider_id,
                description="Description with empty fields",
                price=Decimal("100.00"),
            )

        with pytest.raises(ValidationError):
            # Test case 2: Both name empty and service_id not filed
            CreateProviderServiceInputDTO(
                name="  ",
                provider_id=provider_id,
                description="Description with filled fields",
                price=Decimal("100.00"),
            )

        with pytest.raises(ValidationError):
            # Test case 3: Both name and service_id are filled
            CreateProviderServiceInputDTO(
                name="service 1",
                provider_id=provider_id,
                description="Description with filled fields",
                price=Decimal("100.00"),
                service_id=uuid4(),  # Filled service_id
            )
