from datetime import datetime, timezone

from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActiveError,
)
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.activate_user.activate_user_dto import (
    ActivateUserInputDTO,
    ActivateUserOutputDTO,
)


class ActivateUserUseCase(UseCaseInterface):
    def __init__(
        self,
        user_repository: userRepositoryInterface,
        password_hasher: PasswordHasherInterface,
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def execute(self, input: ActivateUserInputDTO) -> ActivateUserOutputDTO:
        user = self.user_repository.find_user_by_email(email = input.email)

        if user.is_active:
            raise UserAlreadyActiveError(user.email)

        if user.activation_code is None or user.activation_code_expires_at is None:
            raise InvalidActivationCodeError()

        now = datetime.now(timezone.utc)
        
        if now > user.activation_code_expires_at.replace(tzinfo=timezone.utc):
            raise ActivationCodeExpiredError()

        if not self.password_hasher.verify(password= input.activation_code, hashed_password = user.activation_code):
            raise InvalidActivationCodeError()

        user.activate()
        self.user_repository.update_user(user=user)

        return ActivateUserOutputDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            roles=sorted(list(user.roles)),
        )
