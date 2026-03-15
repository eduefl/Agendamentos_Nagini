

from unittest.mock import MagicMock
from uuid import UUID

from usecases.user.list_users.list_users_dto import ListUsersInputDTO
from usecases.user.list_users.list_users_usecase import ListUsersUseCase
from domain.user.user_repository_interface import userRepositoryInterface



class TestMockListUsersUseCase:
	def test_list_users_usecase(self, make_user):
		mock_user_repository = MagicMock(spec = userRepositoryInterface)
		name1 = "Fulano"	
		name2 = "Beltrano"	

		mock_user_repository.list_users.return_value = [make_user(name=name1), 
												  		make_user(name=name2)]
		use_case = ListUsersUseCase(mock_user_repository)

		input_dto =  ListUsersInputDTO()
		output = use_case.execute(input = input_dto)

		assert len(output.users) == 2
		assert {t.name for t in output.users} == {name1, name2}
		mock_user_repository.list_users.assert_called_once()
		assert  mock_user_repository.list_users.call_count == 1
		assert isinstance(output.users, list)
		assert all(isinstance(u.name, str) for u in output.users)
		assert all(isinstance(u.id, UUID) for u in output.users)
		


	def test_list_users_usecase_empty(self):
		mock_user_repository = MagicMock(spec = userRepositoryInterface)
		mock_user_repository.list_users.return_value = []
		use_case = ListUsersUseCase(mock_user_repository)

		input_dto =  ListUsersInputDTO()
		output = use_case.execute(input = input_dto)

		# Asert
		mock_user_repository.list_users.assert_called_once()
		assert  mock_user_repository.list_users.call_count == 1
		assert output.users == []


		
