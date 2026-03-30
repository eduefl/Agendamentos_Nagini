from sqlalchemy.exc import IntegrityError
from sre_constants import IN
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from domain.service.provider_service_entity import ProviderService
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)


class TestProviderServiceSqlalchemyRepository:

    def test_create_provider_service(self, make_provider_service, tst_db_session):
        session = tst_db_session
        provider_service = make_provider_service()
        repository = ProviderServiceRepository(session=session)

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
        self, make_provider_service, tst_db_session
    ):
        session = tst_db_session
        provider_id = uuid4()
        service_id = uuid4()

        provider_service = make_provider_service(
            provider_id=provider_id,
            service_id=service_id,
        )
        repository = ProviderServiceRepository(session=session)

        repository.create_provider_service(provider_service)

        result = repository.find_by_provider_and_service(provider_id, service_id)

        assert result is not None
        assert result.provider_id == provider_id
        assert result.service_id == service_id

    def test_find_by_provider_and_service_not_found(self, tst_db_session):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)
        provider_id = uuid4()
        service_id = uuid4()

        result = repository.find_by_provider_and_service(provider_id, service_id)

        assert result is None

    def test_list_by_provider_id(self, make_provider_service, tst_db_session):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)
        provider_id = uuid4()
        anothet_provider_id = uuid4()
        provider_service = make_provider_service(
            provider_id=provider_id,
            price=Decimal("150.00"),
        )
        repository.create_provider_service(provider_service)
        provider_service2 = make_provider_service(
            provider_id=provider_id,
            price=Decimal("200.00"),
        )
        repository.create_provider_service(provider_service2)

        provider_service3 = make_provider_service(
            provider_id=anothet_provider_id,
            price=Decimal("300.00"),
        )   

        repository.create_provider_service(provider_service3)


        result = repository.list_by_provider_id(provider_id)

        assert len(result) == 2
        assert result[0].provider_id == provider_id
        assert result[0].price == Decimal("150.00")
        assert result[1].price == Decimal("200.00")
        assert result[0].created_at is not None
        assert result[1].created_at is not None
        assert result[0].created_at <= datetime.utcnow()
        assert result[1].created_at <= datetime.utcnow()
        assert result[0].created_at != result[1].created_at
        assert all(ps.provider_id != anothet_provider_id for ps in result)

    def test_create_provider_service_duplicate_constraint(
        self, make_provider_service, tst_db_session
    ):
        session = tst_db_session
        repository = ProviderServiceRepository(session=session)
        provider_id = uuid4()
        service_id = uuid4()

        provider_service1 = make_provider_service(
            provider_id=provider_id,
            service_id=service_id,
        )

        provider_service2 = make_provider_service(
            provider_id=provider_id,
            service_id=service_id,
        )

        repository.create_provider_service(provider_service1)

        with pytest.raises(IntegrityError):
            repository.create_provider_service(provider_service2)
