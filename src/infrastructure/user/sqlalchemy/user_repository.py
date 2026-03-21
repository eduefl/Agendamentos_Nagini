from typing import List
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from domain.user.user_entity import User
from domain.user.user_exceptions import UserNotFoundError, EmailAlreadyExistsError
from domain.user.user_repository_interface import userRepositoryInterface
from infrastructure.user.sqlalchemy.user_model import UserModel


class userRepository(userRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def add_user(self, user: User) -> None:
        user_model = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
        )
        self.session.add(user_model)

        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            # aqui você pode inspecionar a mensagem/constraint, mas por enquanto:
            raise EmailAlreadyExistsError(user.email) from e

        return None


    def find_user_by_id(self, user_id: UUID) -> User:
		# user_in_db: UserModel = self.session.query(UserModel).get(user_id) # get is deprecated, use filter instead
		#user_in_db: UserModel = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        user_in_db = self.session.get(UserModel, user_id)
        if not user_in_db:
            raise UserNotFoundError(user_id)

        return User(
            id=user_in_db.id,
            name=user_in_db.name,
            email=user_in_db.email,
            hashed_password=user_in_db.hashed_password,
            is_active=user_in_db.is_active,
        )

    def list_users(self) -> List[User]:
        users_in_db: List[UserModel] = self.session.query(UserModel).all()
        return [
            User(
                id=u.id,
                name=u.name,
                email=u.email,
                hashed_password=u.hashed_password,
                is_active=u.is_active,
            )
            for u in users_in_db
        ]


    def update_user(self, user: User) -> None:
        try:
            row = self.session.get(UserModel, user.id)
            if not row:
                raise UserNotFoundError(user.id)

            row.name = user.name
            row.email = user.email
            row.hashed_password = user.hashed_password
            row.is_active = user.is_active

            self.session.commit()

        except IntegrityError as e:
            self.session.rollback()
            raise EmailAlreadyExistsError(user.email) from e

