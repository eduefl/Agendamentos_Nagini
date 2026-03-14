from uuid import UUID

from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_user_dto import AddUserInputDTO, AddUserOutputDTO
from usecases.user.add_user.add_user_usecase import AddUserUseCase



class TestAddUserUseCase:

	# teste para criar um usuario com dados valido
	def test_create_user_valid(self,tst_db_session):
		session = tst_db_session
		# repositorio 
		repository = userRepository(session=session)

		# caso de uso
		use_case = AddUserUseCase(repository)	

		# input(request)
		input_dto  = AddUserInputDTO(name="John Doe")
		

		# output(response)
		output = use_case.execute(input = input_dto )

		# verificações

		assert len(repository.list_users()) == 1
		assert output.id is not None
		assert repository.find_user_by_id(output.id)
		assert isinstance(output, AddUserOutputDTO)
		assert isinstance(output.id, UUID)
		assert output.name == "John Doe"
		
		

		



