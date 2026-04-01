from uuid import uuid4


from domain.service.service_entity import Service

from infrastructure.service.sqlalchemy.service_repository import ServiceRepository

from usecases.service.list_services.list_services_dto import ListServicesInputDTO, ListServicesOutputItemDTO
from usecases.service.list_services.list_services_usecase import ListServicesUseCase


class TestListServicesUseCaseIntegration:
    def test_should_list_services_using_real_sqlalchemy_repository(
        self, tst_db_session
    ):
        session = tst_db_session
        service_1 = Service(
            id=uuid4(),
            name="Banho e Tosa",
            description="Serviço para pets",
        )
        service_2 = Service(
            id=uuid4(),
            name="Limpeza Residencial",
            description="Serviço de limpeza completa",
        )

        repository = ServiceRepository(session)
        repository.create_service(service_1)
        repository.create_service(service_2)
        session.commit()

        usecase = ListServicesUseCase(service_repository=repository)

        output = usecase.execute(input=ListServicesInputDTO())

        assert len(output) == 2
        assert isinstance(output[0], ListServicesOutputItemDTO)
        assert isinstance(output[1], ListServicesOutputItemDTO)

        assert output[0].name == "Banho e Tosa"
        assert output[0].description == "Serviço para pets"

        assert output[1].name == "Limpeza Residencial"
        assert output[1].description == "Serviço de limpeza completa"

    def test_should_return_empty_list_when_there_are_no_services(self, tst_db_session):
        session = tst_db_session
        repository = ServiceRepository(session)
        usecase = ListServicesUseCase(service_repository=repository)

        output = usecase.execute(input=ListServicesInputDTO())

        assert output == []
