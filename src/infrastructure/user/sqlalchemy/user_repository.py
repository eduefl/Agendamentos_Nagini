from typing import List, Set
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.user.user_entity import User
from domain.user.user_exceptions import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    RolesRequiredError,
    RoleRemovalNotAllowedError,
    UserNotFoundError,
)
from domain.user.user_repository_interface import userRepositoryInterface
from infrastructure.user.sqlalchemy.user_model import RoleModel, UserModel


class userRepository(userRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _get_role_by_name(self, role_name: str) -> RoleModel:
        name = role_name.strip().lower()
        role = self.session.query(RoleModel).filter(RoleModel.name == name).one_or_none()
        if not role:
            raise RoleNotFoundError(name)
        return role

    def add_user(self, user: User) -> None:
        # regra: roles são obrigatórios
        if not user.roles or len(user.roles) == 0:
            raise RolesRequiredError()

        user_model = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
        )

        # aplica roles informados (obrigatório)
        for role_name in user.roles:
            role = self._get_role_by_name(role_name)
            user_model.roles.append(role)

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

        roles = {r.name for r in (user_in_db.roles or [])}

        return User(
            id=user_in_db.id,
            name=user_in_db.name,
            email=user_in_db.email,
            hashed_password=user_in_db.hashed_password,
            is_active=user_in_db.is_active,
            roles=roles,
        )

    def list_users(self) -> List[User]:
        users_in_db: List[UserModel] = self.session.query(UserModel).all()
        result: List[User] = []

        for u in users_in_db:
            roles = {r.name for r in (u.roles or [])}
            result.append(
                User(
                    id=u.id,
                    name=u.name,
                    email=u.email,
                    hashed_password=u.hashed_password,
                    is_active=u.is_active,
                    roles=roles,
                )
            )

        return result

    def update_user(self, user: User) -> None:
        try:
            row = self.session.get(UserModel, user.id)
            if not row:
                raise UserNotFoundError(user.id)

            row.name = user.name
            row.email = user.email
            row.hashed_password = user.hashed_password
            row.is_active = user.is_active

            # regras: update_user não mexe em roles
            self.session.commit()

        except IntegrityError as e:
            self.session.rollback()
            raise EmailAlreadyExistsError(user.email) from e

        return None

    # --- roles ---
    def list_user_roles(self, user_id: UUID) -> Set[str]:
        user_in_db = self.session.get(UserModel, user_id)
        if not user_in_db:
            raise UserNotFoundError(user_id)
        return {r.name for r in (user_in_db.roles or [])}

    def add_role_to_user(self, user_id: UUID, role_name: str) -> None:
        user_in_db = self.session.get(UserModel, user_id)
        if not user_in_db:
            raise UserNotFoundError(user_id)

        role = self._get_role_by_name(role_name)

        # não duplica
        if any(r.id == role.id for r in (user_in_db.roles or [])):
            return None

        user_in_db.roles.append(role)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
        return None

    def remove_role_from_user(self, user_id: UUID, role_name: str) -> None:
        # regra: nunca remover role
        user_in_db = self.session.get(UserModel, user_id)
        if not user_in_db:
            raise UserNotFoundError(user_id)
        raise RoleRemovalNotAllowedError(role_name)