from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestProviderServiceSqlalchemyRepository:
    @staticmethod
    def _create_persisted_provider(session, make_user):
        repo = userRepository(session=session)
        provider = make_user(
            id=uuid4(),
            name=f"Prestador {uuid4()}",
            email=f"{uuid4()}@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        repo.add_user(provider)
        return provider

    @staticmethod
    def _create_persisted_service(session, service_id=None, name=None, description=None):
        service = ServiceModel(
            id=service_id or uuid4(),
            name=name or f"Serviço {uuid4()}",
            description=description or "Descrição do serviço",
        )
        session.add(service)
        session.commit()
        return service

    def test_create_provider_service(
        self,
        make_provider_service,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)

        provider = self._create_persisted_provider(session, make_user)
        service = self._create_persisted_service(session)

        provider_service = make_provider_service(
            provider_id=provider.id,
            service_id=service.id,
        )

        repository.create_provider_service(provider_service=provider_service)

        assert session.query(ProviderServiceModel).count() == 1
        row = (
            session.query(ProviderServiceModel)
            .filter(ProviderServiceModel.id == provider_service.id)
            .one()
        )
        assert row.id == provider_service.id
        assert row.provider_id == provider_service.provider_id
        assert row.service_id == provider_service.service_id
        assert row.price == provider_service.price
        assert row.active == provider_service.active
        assert row.created_at is not None

    def test_find_by_provider_and_service_found(
        self,
        make_provider_service,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)

        provider = self._create_persisted_provider(session, make_user)
        service = self._create_persisted_service(session)

        provider_service = make_provider_service(
            provider_id=provider.id,
            service_id=service.id,
        )

        repository.create_provider_service(provider_service)

        result = repository.find_by_provider_and_service(provider.id, service.id)

        assert result is not None
        assert result.provider_id == provider.id
        assert result.service_id == service.id

    def test_find_by_provider_and_service_not_found(self, tst_db_session):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)
        provider_id = uuid4()
        service_id = uuid4()

        result = repository.find_by_provider_and_service(provider_id, service_id)

        assert result is None

    def test_list_by_provider_id(
        self,
        make_provider_service,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)

        provider = self._create_persisted_provider(session, make_user)
        another_provider = self._create_persisted_provider(session, make_user)

        service1 = self._create_persisted_service(
            session,
            name="Serviço 1",
            description="Descrição 1",
        )
        service2 = self._create_persisted_service(
            session,
            name="Serviço 2",
            description="Descrição 2",
        )
        service3 = self._create_persisted_service(
            session,
            name="Serviço 3",
            description="Descrição 3",
        )

        provider_service1 = make_provider_service(
            provider_id=provider.id,
            service_id=service1.id,
            price=Decimal("150.00"),
        )
        provider_service2 = make_provider_service(
            provider_id=provider.id,
            service_id=service2.id,
            price=Decimal("200.00"),
        )
        provider_service3 = make_provider_service(
            provider_id=another_provider.id,
            service_id=service3.id,
            price=Decimal("300.00"),
        )

        repository.create_provider_service(provider_service1)
        repository.create_provider_service(provider_service2)
        repository.create_provider_service(provider_service3)

        result = repository.list_by_provider_id(provider.id)

        assert len(result) == 2
        assert result[0].provider_id == provider.id
        assert result[0].price == Decimal("150.00")
        assert result[1].price == Decimal("200.00")
        assert result[0].created_at is not None
        assert result[1].created_at is not None
        assert result[0].created_at <= datetime.utcnow()
        assert result[1].created_at <= datetime.utcnow()
        assert result[0].created_at != result[1].created_at
        assert all(ps.provider_id != another_provider.id for ps in result)

        returned_service_ids = {item.service_id for item in result}
        assert provider_service1.service_id in returned_service_ids
        assert provider_service2.service_id in returned_service_ids

        returned_names = {item.service_name for item in result}
        assert "Serviço 1" in returned_names
        assert "Serviço 2" in returned_names

    def test_create_provider_service_duplicate_constraint(
        self,
        make_provider_service,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)

        provider = self._create_persisted_provider(session, make_user)
        service = self._create_persisted_service(session)

        provider_service1 = make_provider_service(
            provider_id=provider.id,
            service_id=service.id,
        )

        provider_service2 = make_provider_service(
            provider_id=provider.id,
            service_id=service.id,
        )

        repository.create_provider_service(provider_service1)

        with pytest.raises(IntegrityError):
            repository.create_provider_service(provider_service2)