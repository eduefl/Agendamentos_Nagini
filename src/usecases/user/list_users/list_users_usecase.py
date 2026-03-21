from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.list_users.list_users_dto import (
    ListUsersInputDTO,
    ListUsersOutputDTO,
    UserDto,
)


class ListUsersUseCase(UseCaseInterface):
    def __init__(self, user_repository: userRepositoryInterface):
        self.user_repository = user_repository

    def execute(self, input: ListUsersInputDTO) -> ListUsersOutputDTO:
        users = self.user_repository.list_users()

        users_dto = [
            UserDto(
                id=user.id,
                name=user.name,
                email=user.email,
                is_active=user.is_active,
            )
            for user in users
        ]

        return ListUsersOutputDTO(users=users_dto)