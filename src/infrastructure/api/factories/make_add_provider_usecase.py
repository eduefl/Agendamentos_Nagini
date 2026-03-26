from usecases.user.add_user.add_prestador_usecase import AddPrestadorUseCase
from infrastructure.notification.smtp_email_sender import SMTPEmailSender
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from sqlalchemy.orm import Session

def make_add_provider_usecase(session: Session) -> AddPrestadorUseCase:
    return AddPrestadorUseCase(
        user_repository=userRepository(session=session),
        password_hasher=PasslibPasswordHasher(),
        email_sender=SMTPEmailSender(),
    )