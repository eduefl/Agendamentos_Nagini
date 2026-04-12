from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.find_user_by_id.find_user_by_id_dto import (
    findUserByIdInputDTO,
    findUserByIdOutputDTO,
)


class FindUserByIdUseCase(UseCaseInterface):
    def __init__(
        self,
        user_repository: userRepositoryInterface,
    ):
        self.user_repository = user_repository

    def execute(self, input: findUserByIdInputDTO) -> findUserByIdOutputDTO:
        user = self.user_repository.find_user_by_id(user_id=input.id)


        return findUserByIdOutputDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            roles=sorted(list(user.roles)),
        )