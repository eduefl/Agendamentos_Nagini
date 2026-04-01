# tests/usecases/service/list_services/test_list_services_usecase.py
from uuid import uuid4
from unittest.mock import Mock

from domain.service.service_repository_interface import ServiceRepositoryInterface
from usecases.service.list_services.list_services_dto import ListServicesInputDTO, ListServicesOutputItemDTO
from usecases.service.list_services.list_services_usecase import ListServicesUseCase


class TestListServicesUseCase:
    def test_should_return_list_of_services_output_dto(self):
        service_id_1 = uuid4()
        service_id_2 = uuid4()

        service_1 = Mock()
        service_1.id = service_id_1
        service_1.name = "limpeza residencial"
        service_1.description = "Serviço de limpeza completa"

        service_2 = Mock()
        service_2.id = service_id_2
        service_2.name = "banho e tosa"
        service_2.description = "Serviço para pets"

        service_repository = Mock(spec=ServiceRepositoryInterface)
        service_repository.list_all.return_value = [service_1, service_2]

        usecase = ListServicesUseCase(service_repository=service_repository)

        output = usecase.execute(input=ListServicesInputDTO())

        service_repository.list_all.assert_called_once_with()
        

        assert len(output) == 2

        assert isinstance(output[0], ListServicesOutputItemDTO)
        assert output[0].service_id == service_id_1
        assert output[0].name == "Limpeza Residencial" #Returns Normalized
        assert output[0].description == "Serviço de limpeza completa"

        assert isinstance(output[1], ListServicesOutputItemDTO)
        assert output[1].service_id == service_id_2
        assert output[1].name == "Banho e Tosa" #Returns Normalized
        assert output[1].description == "Serviço para pets"

    def test_should_return_empty_list_when_there_are_no_services(self):
        service_repository = Mock(spec=ServiceRepositoryInterface)
        service_repository.list_all.return_value = []

        usecase = ListServicesUseCase(service_repository=service_repository)

        output = usecase.execute(input=ListServicesInputDTO())

        service_repository.list_all.assert_called_once_with()
        assert output == []
