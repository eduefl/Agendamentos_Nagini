from infrastructure.notification.smtp_email_sender import SMTPEmailSender
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_cliente_usecase import AddClientUseCase
from sqlalchemy.orm import Session

def make_add_client_usecase(session: Session) -> AddClientUseCase:
    return AddClientUseCase(
        user_repository=userRepository(session=session),
        password_hasher=PasslibPasswordHasher(),
        email_sender=SMTPEmailSender(),
    )