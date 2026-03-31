from decimal import Decimal
from uuid import uuid4

import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.user.user_exceptions import UserNotFoundError
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.list_provider_services.list_provider_services_dto import (
    ListProviderServicesInputDTO,
    ListProviderServicesOutputDTO,
)
from usecases.service.list_provider_services.list_provider_services_usecase import (
    ListProviderServicesUseCase,
)


class TestListProviderServicesUseCaseIntegration:
    def test_list_provider_services_success(
        self,
        tst_db_session,
        make_user,
        make_provider_service,
        seed_roles,
    ):
        session = tst_db_session

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
        session.commit()

        provider_service_1 = make_provider_service(
            provider_id=provider_id,
            price=Decimal("100.00"),
        )
        provider_service_2 = make_provider_service(
            provider_id=provider_id,
            price=Decimal("150.00"),
        )

        service_1 = ServiceModel(
            id=provider_service_1.service_id,
            name="Test Service",
            description="Test Description",
        )
        service_2 = ServiceModel(
            id=provider_service_2.service_id,
            name="Another Service",
            description="Another Description",
        )

        session.add_all([service_1, service_2])
        session.commit()

        provider_service_repository.create_provider_service(provider_service_1)
        provider_service_repository.create_provider_service(provider_service_2)

        use_case = ListProviderServicesUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        output = use_case.execute(input_dto)

        assert isinstance(output, ListProviderServicesOutputDTO)
        assert len(output.items) == 2

        returned_names = {item.service_name for item in output.items}
        assert "Test Service" in returned_names
        assert "Another Service" in returned_names

        returned_descriptions = {item.description for item in output.items}
        assert "Test Description" in returned_descriptions
        assert "Another Description" in returned_descriptions

        returned_prices = {item.price for item in output.items}
        assert Decimal("100.00") in returned_prices
        assert Decimal("150.00") in returned_prices

        assert all(item.provider_id == provider_id for item in output.items)
        assert all(item.active is True for item in output.items)

    def test_list_provider_services_user_not_found(
        self,
        tst_db_session,
    ):
        session = tst_db_session

        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        use_case = ListProviderServicesUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ListProviderServicesInputDTO(provider_id=uuid4())

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

    def test_list_provider_services_no_services(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session

        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider_id = uuid4()

        provider = make_user(
            id=provider_id,
            name="Prestador sem servicos",
            email="prestador_sem_servicos@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        use_case = ListProviderServicesUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        output = use_case.execute(input_dto)

        assert isinstance(output, ListProviderServicesOutputDTO)
        assert output.items == []

    def test_list_provider_services_provider_inactive(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session

        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider_id = uuid4()

        inactive_provider = make_user(
            id=provider_id,
            name="Prestador Inativo",
            email="prestador_inativo@example.com",
            hashed_password="hashed_password",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(inactive_provider)
        session.commit()

        use_case = ListProviderServicesUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ListProviderServicesInputDTO(provider_id=provider_id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_list_provider_services_user_not_prestador(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session

        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        user_id = uuid4()

        client_user = make_user(
            id=user_id,
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

        use_case = ListProviderServicesUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ListProviderServicesInputDTO(provider_id=user_id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)