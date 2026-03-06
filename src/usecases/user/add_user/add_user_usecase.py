from typing import Any
from uuid import uuid4
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from domain.__seedwork.use_case_interface import UseCaseInterface
from usecases.user.add_user.add_user_dto import AddUserInputDTO, AddUserOutputDTO

class AddUserUseCase(UseCaseInterface):
	def __init__(self, user_repository: userRepositoryInterface):
		self.user_repository = user_repository
		
	def execute(self, input: AddUserInputDTO ) -> AddUserOutputDTO:
		# 1. Criar a entidade User
		user = User(id=uuid4(), name=input.name)
		
		# 2. Salvar a entidade usando o repositório
		self.user_repository.add_user(user = user)
		
		# 3. Retornar o output DTO
		return AddUserOutputDTO(id=user.id, name=user.name)
