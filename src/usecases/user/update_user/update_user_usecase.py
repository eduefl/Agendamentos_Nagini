from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.update_user.update_user_dto import UpdateUserInputDTO, UpdateUserOutputDTO


class updateUserUsecase(UseCaseInterface):
    def __init__(self, user_repository: userRepositoryInterface):
        self.user_repository = user_repository

    def execute(self, input: UpdateUserInputDTO) -> UpdateUserOutputDTO:
        user = self.user_repository.find_user_by_id(user_id=input.id)

        # update parcial (só muda o que veio no DTO)
        if input.name is not None:
            user.name = input.name

        if input.email is not None:
            user.email = str(input.email)

        if input.is_active is not None:
            user.is_active = input.is_active

        self.user_repository.update_user(user=user)

        return UpdateUserOutputDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
        )