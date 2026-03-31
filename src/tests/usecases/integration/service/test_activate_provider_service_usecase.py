from decimal import Decimal
from uuid import uuid4

import pytest

from domain.__seedwork.exceptions import ForbiddenError
from domain.service.service_exceptions import (
    
    ProviderServiceAlreadyActiveError,
    ProviderServiceNotFoundError,
)
from domain.user.user_exceptions import UserNotFoundError
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service.activate_provider_service.activate_provider_service_dto import (
    ActivateProviderServiceInputDTO,
    ActivateProviderServiceOutputDTO,
)
from usecases.service.activate_provider_service.activate_provider_service_usecase import (
    ActivateProviderServiceUseCase,
)


class TestActivateProviderServiceUseCaseIntegration:
    def test_activate_provider_service_success(
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
            name="Prestador",
            email="prestador@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        provider_service = make_provider_service(
            provider_id=provider_id,
            price=Decimal("100.00"),
            active=False,
        )

        service = ServiceModel(
            id=provider_service.service_id,
            name="Servico teste",
            description="Descricao teste",
        )
        session.add(service)
        session.commit()

        provider_service_repository.create_provider_service(provider_service)

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_id,
            provider_service_id=provider_service.id,
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, ActivateProviderServiceOutputDTO)
        assert output.provider_service_id == provider_service.id
        assert output.active is True

        updated = provider_service_repository.find_by_id(provider_service.id)
        assert updated is not None
        assert updated.active is True

    def test_activate_provider_service_user_not_found(self, tst_db_session):
        session = tst_db_session
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=uuid4(),
            provider_service_id=uuid4(),
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

    def test_activate_provider_service_provider_inactive(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador Inativo",
            email="prestador_inativo@example.com",
            hashed_password="hashed_password",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider.id,
            provider_service_id=uuid4(),
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_activate_provider_service_user_not_provider(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        user = make_user(
            id=uuid4(),
            name="Cliente",
            email="cliente@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(user)
        session.commit()

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=user.id,
            provider_service_id=uuid4(),
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_activate_provider_service_not_found(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador",
            email="prestador@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider.id,
            provider_service_id=uuid4(),
        )

        with pytest.raises(ProviderServiceNotFoundError):
            use_case.execute(input_dto)

    def test_activate_provider_service_from_another_provider(
        self,
        tst_db_session,
        make_user,
        make_provider_service,
        seed_roles,
    ):
        session = tst_db_session
        provider_service_repository = ProviderServiceRepository(session=session)
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

        provider_service = make_provider_service(
            provider_id=provider_b.id,
            price=Decimal("100.00"),
            active=False,
        )

        service = ServiceModel(
            id=provider_service.service_id,
            name="Servico de B",
            description="Descricao",
        )
        session.add(service)
        session.commit()

        provider_service_repository.create_provider_service(provider_service)

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider_a.id,
            provider_service_id=provider_service.id,
        )

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

    def test_activate_provider_service_already_active(
        self,
        tst_db_session,
        make_user,
        make_provider_service,
        seed_roles,
    ):
        session = tst_db_session
        provider_service_repository = ProviderServiceRepository(session=session)
        user_repository = userRepository(session=session)

        provider = make_user(
            id=uuid4(),
            name="Prestador",
            email="prestador@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repository.add_user(provider)
        session.commit()

        provider_service = make_provider_service(
            provider_id=provider.id,
            price=Decimal("100.00"),
            active=True,
        )

        service = ServiceModel(
            id=provider_service.service_id,
            name="Servico teste",
            description="Descricao teste",
        )
        session.add(service)
        session.commit()

        provider_service_repository.create_provider_service(provider_service)

        use_case = ActivateProviderServiceUseCase(
            provider_service_repository=provider_service_repository,
            user_repository=user_repository,
        )

        input_dto = ActivateProviderServiceInputDTO(
            provider_id=provider.id,
            provider_service_id=provider_service.id,
        )

        with pytest.raises(ProviderServiceAlreadyActiveError):
            use_case.execute(input_dto)
