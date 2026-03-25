from typing import Any, Dict, List, Set
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

    def _to_entity(self, user_model: UserModel) -> User:
        roles = {r.name for r in (user_model.roles or [])}

        return User(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            hashed_password=user_model.hashed_password,
            is_active=user_model.is_active,
            activation_code=user_model.activation_code,
            activation_code_expires_at=user_model.activation_code_expires_at,
            roles=roles,
        )

    def _to_model_data(self, user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
            "activation_code": user.activation_code,
            "activation_code_expires_at": user.activation_code_expires_at,
        }

    def add_user(self, user: User) -> None:
        # regra: roles são obrigatórios
        if not user.roles or len(user.roles) == 0:
            raise RolesRequiredError()

        user_model = UserModel(**self._to_model_data(user))

        # aplica roles informados (obrigatório)
        for role_name in user.roles:
            role = self._get_role_by_name(role_name)
            user_model.roles.append(role)

        self.session.add(user_model)

        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise EmailAlreadyExistsError(user.email) from e

        return None


    def find_user_by_id(self, user_id: UUID) -> User:
		# user_in_db: UserModel = self.session.query(UserModel).get(user_id) # get is deprecated, use filter instead
		#user_in_db: UserModel = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        user_in_db = self.session.get(UserModel, user_id)
        if not user_in_db:
            raise UserNotFoundError(user_id)

        return self._to_entity(user_in_db)
    
    def find_user_by_email(self, email: str) -> User:        
        user_in_db = self.session.query(UserModel).filter(UserModel.email == email.strip().lower()).one_or_none()
        if not user_in_db:
            raise UserNotFoundError(email, attribute="email")

        return self._to_entity(user_in_db)

    def list_users(self) -> List[User]:
        users_in_db: List[UserModel] = self.session.query(UserModel).all()
        return [self._to_entity(user_model) for user_model in users_in_db]

    def update_user(self, user: User) -> None:
        try:
            row = self.session.get(UserModel, user.id)
            if not row:
                raise UserNotFoundError(user.id)

            model_data = self._to_model_data(user)

            row.name = model_data["name"]
            row.email = model_data["email"]
            row.hashed_password = model_data["hashed_password"]
            row.is_active = model_data["is_active"]
            row.activation_code = model_data["activation_code"]
            row.activation_code_expires_at = model_data["activation_code_expires_at"]

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