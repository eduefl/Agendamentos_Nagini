from infrastructure.security.factories.make_token_service import make_token_service
from usecases.user.authenticate_user.authenticate_user_usecase import AuthenticateUserUseCase
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from sqlalchemy.orm import Session

def make_authenticate_user_usecase(session: Session) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(
        user_repository = userRepository(session=session),
        password_hasher = PasslibPasswordHasher(),
        tokenService     = make_token_service(),
    )