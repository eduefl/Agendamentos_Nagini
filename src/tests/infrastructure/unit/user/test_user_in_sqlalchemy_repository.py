from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from domain.user.user_exceptions import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    RoleRemovalNotAllowedError,
    RolesRequiredError,
    UserNotFoundError,
)
from infrastructure.user.sqlalchemy.user_model import UserModel
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestUserSqlalchemyRepository:
    def test_add_user_persists_in_db(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        expires_at = datetime.now() + timedelta(minutes=15)
        user = make_user(
            roles={"cliente"},
            is_active=False,
            activation_code="abc12345",
            activation_code_expires_at=expires_at,
        )

        repo.add_user(user=user)

        row = session.query(UserModel).filter(UserModel.id == user.id).one()

        assert row.id == user.id
        assert row.name == user.name
        assert row.email == user.email
        assert row.hashed_password == user.hashed_password
        assert row.is_active == user.is_active
        assert row.activation_code == user.activation_code
        assert row.activation_code_expires_at == user.activation_code_expires_at
        assert {r.name for r in (row.roles or [])} == {"cliente"}

    def test_find_user_by_id_returns_domain_entity(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        expires_at = datetime.now() + timedelta(minutes=15)
        user = make_user(
            roles={"cliente"},
            activation_code="abc12345",
            activation_code_expires_at=expires_at,
        )

        row = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            activation_code=user.activation_code,
            activation_code_expires_at=user.activation_code_expires_at,
        )
        row.roles.extend(
            [
                repo._get_role_by_name("cliente"),
            ]
        )

        session.add(row)
        session.commit()

        found = repo.find_user_by_id(user_id=user.id)

        assert found.id == user.id
        assert found.name == user.name
        assert found.email == user.email
        assert found.hashed_password == user.hashed_password
        assert found.is_active == user.is_active
        assert found.activation_code == user.activation_code
        assert found.activation_code_expires_at == user.activation_code_expires_at
        assert found.roles == {"cliente"}


    def test_find_user_by_id_raises_when_not_found(self, tst_db_session):
        session = tst_db_session
        repo = userRepository(session=session)

        with pytest.raises(UserNotFoundError):
            repo.find_user_by_id(user_id=uuid4())

    def test_find_user_by_email_returns_domain_entity(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        expires_at = datetime.now() + timedelta(minutes=15)
        user = make_user(roles={"cliente"}, 
                         activation_code="abc12345", 
                         activation_code_expires_at=expires_at,
                         email = "test@test.com.ts")
        row = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            activation_code=user.activation_code,
            activation_code_expires_at=user.activation_code_expires_at,
        )
        row.roles.extend(
            [
                repo._get_role_by_name("cliente"),
            ]
        )
        
        session.add(row)
        session.commit()

        found = repo.find_user_by_email(email=user.email)

        assert found.id == user.id
        assert found.name == user.name
        assert found.email == user.email
        assert found.hashed_password == user.hashed_password
        assert found.is_active == user.is_active
        assert found.activation_code == user.activation_code
        assert found.activation_code_expires_at == user.activation_code_expires_at
        assert found.roles == {"cliente"}




    def test_find_user_by_email_raises_when_not_found(self, tst_db_session):
        session = tst_db_session
        repo = userRepository(session=session)
        with pytest.raises(UserNotFoundError):
            repo.find_user_by_email("test@test.com")

    def test_list_users_returns_all_users(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        expires_at_1 = datetime.now() + timedelta(minutes=15)
        expires_at_2 = datetime.now() + timedelta(minutes=30)

        user1 = make_user(
            email="user1@example.com",
            roles={"cliente"},
            activation_code="code1111",
            activation_code_expires_at=expires_at_1,
        )
        user2 = make_user(
            email="user2@example.com",
            roles={"prestador"},
            activation_code="code2222",
            activation_code_expires_at=expires_at_2,
        )

        row1 = UserModel(
            id=user1.id,
            name=user1.name,
            email=user1.email,
            hashed_password=user1.hashed_password,
            is_active=user1.is_active,
            activation_code=user1.activation_code,
            activation_code_expires_at=user1.activation_code_expires_at,
        )
        row1.roles.extend([repo._get_role_by_name("cliente")])

        row2 = UserModel(
            id=user2.id,
            name=user2.name,
            email=user2.email,
            hashed_password=user2.hashed_password,
            is_active=user2.is_active,
            activation_code=user2.activation_code,
            activation_code_expires_at=user2.activation_code_expires_at,
        )
        row2.roles.extend([repo._get_role_by_name("prestador")])

        session.add_all([row1, row2])
        session.commit()

        users = repo.list_users()

        assert len(users) == 2

        assert any(
            u.id == user1.id
            and u.name == user1.name
            and u.email == user1.email
            and u.is_active == user1.is_active
            and u.activation_code == user1.activation_code
            and u.activation_code_expires_at == user1.activation_code_expires_at
            and u.roles == {"cliente"}
            for u in users
        )

        assert any(
            u.id == user2.id
            and u.name == user2.name
            and u.email == user2.email
            and u.is_active == user2.is_active
            and u.activation_code == user2.activation_code
            and u.activation_code_expires_at == user2.activation_code_expires_at
            and u.roles == {"prestador"}
            for u in users
        )

    def test_update_user_modifies_db(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session

        initial_expires_at = datetime.now() + timedelta(minutes=15)
        updated_expires_at = datetime.now() + timedelta(minutes=30)

        user = make_user(
            roles={"cliente"},
            activation_code="oldcode1",
            activation_code_expires_at=initial_expires_at,
        )

        row = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            activation_code=user.activation_code,
            activation_code_expires_at=user.activation_code_expires_at,
        )

        repo = userRepository(session=session)
        row.roles.extend([repo._get_role_by_name("cliente")])

        session.add(row)
        session.commit()

        user.name = "Updated Name"
        user.email = "updated@example.com"
        user.is_active = True
        user.hashed_password = "updated-hash"
        user.activation_code = "newcode12"
        user.activation_code_expires_at = updated_expires_at

        repo.update_user(user=user)

        updated_row = session.query(UserModel).filter(UserModel.id == user.id).one()
        assert updated_row.name == "Updated Name"
        assert updated_row.email == "updated@example.com"
        assert updated_row.is_active is True
        assert updated_row.hashed_password == "updated-hash"
        assert updated_row.activation_code == "newcode12"
        assert updated_row.activation_code_expires_at == updated_expires_at

    def test_update_user_clears_activation_fields(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        expires_at = datetime.now() + timedelta(minutes=15)
        user = make_user(
            roles={"cliente"},
            activation_code="abc12345",
            activation_code_expires_at=expires_at,
        )

        row = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            activation_code=user.activation_code,
            activation_code_expires_at=user.activation_code_expires_at,
        )
        row.roles.extend([repo._get_role_by_name("cliente")])

        session.add(row)
        session.commit()

        user.activate()
        repo.update_user(user=user)

        updated_row = session.query(UserModel).filter(UserModel.id == user.id).one()
        assert updated_row.is_active is True
        assert updated_row.activation_code is None
        assert updated_row.activation_code_expires_at is None

    def test_update_user_raises_when_not_found(self, make_user, tst_db_session):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user()
        with pytest.raises(UserNotFoundError):
            repo.update_user(user=user)

    def test_add_user_raises_email_already_exists_when_email_duplicate(
        self, make_user, tst_db_session, seed_roles
    ):
        session = tst_db_session
        repo = userRepository(session=session)

        user1 = make_user(email="dup@example.com", roles={"cliente"})
        user2 = make_user(email="dup@example.com", roles={"cliente"})

        repo.add_user(user=user1)

        with pytest.raises(EmailAlreadyExistsError, match="dup@example.com"):
            repo.add_user(user=user2)

    def test_add_user_raises_roles_required_when_missing_roles(
        self, make_user, tst_db_session, seed_roles
    ):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user(roles=set())

        with pytest.raises(RolesRequiredError, match="User roles are required"):
            repo.add_user(user=user)

    def test_add_role_to_user_adds_new_role(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        # cria usuário com role inicial
        user = make_user(email="role-test@example.com", roles={"cliente"})
        repo.add_user(user=user)

        # adiciona nova role
        repo.add_role_to_user(user_id=user.id, role_name="prestador")

        # verifica no banco
        row = session.query(UserModel).filter(UserModel.id == user.id).one()
        assert {r.name for r in (row.roles or [])} == {"cliente", "prestador"}

        # e também garantindo que repo retorna no domínio
        found = repo.find_user_by_id(user_id=user.id)
        assert found.roles == {"cliente", "prestador"}

    def test_remove_role_from_user_raises_forbidden(
        self, make_user, tst_db_session, seed_roles
    ):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user(email="no-remove@example.com", roles={"cliente"})
        repo.add_user(user=user)

        with pytest.raises(RoleRemovalNotAllowedError, match="Role removal is not allowed"):
            repo.remove_role_from_user(user_id=user.id, role_name="cliente")

    def test_add_role_to_user_raises_when_user_not_found(self, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        with pytest.raises(UserNotFoundError):
            repo.add_role_to_user(user_id=uuid4(), role_name="cliente")

    def test_remove_role_from_user_raises_when_user_not_found(self, tst_db_session):
        session = tst_db_session
        repo = userRepository(session=session)

        with pytest.raises(UserNotFoundError):
            repo.remove_role_from_user(user_id=uuid4(), role_name="cliente")

    def test_add_role_to_user_raises_when_role_not_found(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user(email="role-not-found@example.com", roles={"cliente"})
        repo.add_user(user=user)

        with pytest.raises(RoleNotFoundError, match="ghost"):
            repo.add_role_to_user(user_id=user.id, role_name="ghost")

    def test_add_role_to_user_is_idempotent_when_role_already_assigned(
        self, make_user, tst_db_session, seed_roles
    ):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user(email="idempotent@example.com", roles={"cliente"})
        repo.add_user(user=user)

        # adiciona a mesma role novamente (não deve duplicar e nem falhar)
        repo.add_role_to_user(user_id=user.id, role_name="cliente")

        row = session.query(UserModel).filter(UserModel.id == user.id).one()
        roles = [r.name for r in (row.roles or [])]
        assert roles.count("cliente") == 1
        