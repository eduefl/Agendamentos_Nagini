from uuid import uuid4
from domain.service.service_exceptions import ServiceNotFoundError
import pytest




from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository


class TestServiceSqlalchemyRepository:
	def test_add_service_persists_in_db(self, make_service, tst_db_session):
		session = tst_db_session
		service = make_service()
		repo = ServiceRepository(session=session)
		
		repo.create_service(service=service)

		row = session.query(ServiceModel).filter(ServiceModel.id == service.id).one()
		assert row.id == service.id
		assert row.name == service.name
		assert row.description == service.description

	def test_find_by_id_returns_domain_entity(self, make_service, tst_db_session):
		session = tst_db_session
		service = make_service()
		repo = ServiceRepository(session=session)
		repo.create_service(service=service)
		found = repo.find_by_id(service_id=service.id)

		assert found.id == service.id
		assert found.name == service.name
		assert found.description == service.description
	
	def test_find_by_id_raises_when_not_found(self, tst_db_session):
		session = tst_db_session
		repo = ServiceRepository(session=session)
		with pytest.raises(ServiceNotFoundError):
			repo.find_by_id(service_id=uuid4())	

	def test_find_by_name_returns_domain_entity(self, make_service, tst_db_session):
		session = tst_db_session
		service = make_service()
		repo = ServiceRepository(session=session)
		repo.create_service(service=service)
		found = repo.find_by_name(name=service.name)

		assert found.id == service.id
		assert found.name == service.name
		assert found.description == service.description
	
	def test_find_by_name_returns_none_when_not_found(self, tst_db_session):
		session = tst_db_session
		repo = ServiceRepository(session=session)
		found = repo.find_by_name(name="Nonexistent Service")
		assert found is None	
		
	def test_find_by_name_is_case_insensitive(self, make_service, tst_db_session):
		session = tst_db_session
		service = make_service(name="Test Service")
		repo = ServiceRepository(session=session)
		repo.create_service(service=service)
		found = repo.find_by_name(name=" TEST SERVICE ")

		assert found.id == service.id
		assert found.name == service.name
		assert found.description == service.description

	def test_list_all_services(self, make_service, tst_db_session):
		session = tst_db_session
		repo = ServiceRepository(session=session)
		service1 = make_service(name="Service A")
		service2 = make_service(name="Service B")
		repo.create_service(service=service1)
		repo.create_service(service=service2)

		services = repo.list_all()

		assert len(services) == 2
		assert services[0].name == "service a"#always deve retornar em lowercase por causa do _to_entity() e do create_service() que normaliza o nome
		assert services[1].name == "service b"

 

