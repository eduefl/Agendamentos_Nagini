from passlib.context import CryptContext

from domain.security.password_hasher_interface import PasswordHasherInterface


class PasslibPasswordHasher(PasswordHasherInterface):
    def __init__(self) -> None:
        self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return self._ctx.verify(password, hashed_password)