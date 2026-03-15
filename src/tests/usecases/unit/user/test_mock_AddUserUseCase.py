from unittest.mock import MagicMock
from uuid import UUID

from usecases.user.add_user.add_user_dto import AddUserInputDTO, AddUserOutputDTO
from usecases.user.add_user.add_user_usecase import AddUserUseCase
from domain.user.user_repository_interface import userRepositoryInterface  



class TestAddUserUseCase:

	# teste para criar um usuario com dados valido
	def test_mock_create_user_valid(self):
		# repositorio 
		# mock_repository = MagicMock(userRepositoryInterface)
		mock_repository = MagicMock(spec=userRepositoryInterface)

		# caso de uso
		use_case = AddUserUseCase(mock_repository)	

		# input(request)
		input_dto = AddUserInputDTO(name="John Doe")
		

		# output(response)
		output = use_case.execute(input = input_dto)

		# verificações
		assert output.id is not None
		assert isinstance(output, AddUserOutputDTO)
		assert isinstance(output.id, UUID)
		assert isinstance(output.name, str)		
		assert output.name == "John Doe"
		assert mock_repository.add_user.called is True		
		assert mock_repository.add_user.call_count == 1

		



