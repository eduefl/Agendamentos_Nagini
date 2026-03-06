from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.update_user.update_user_dto import  UpdateUserInputDTO, UpdateUserOutputDTO

class updateUserUsecase(UseCaseInterface):

	def __init__(self, user_repository: userRepositoryInterface):
		self.user_repository = user_repository

	def execute(self, input_dto: UpdateUserInputDTO) -> UpdateUserOutputDTO:
		user = self.user_repository.find_user_by_id(input_dto.id)
		user.name = input_dto.name
		self.user_repository.update_user(user)
		return UpdateUserOutputDTO(id=user.id, name=user.name)	
	