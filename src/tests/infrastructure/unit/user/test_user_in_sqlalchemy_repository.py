from uuid import uuid4

import pytest
from domain.user.user_exceptions import (
    EmailAlreadyExistsError,
    RoleRemovalNotAllowedError,
    RolesRequiredError,
    UserNotFoundError,
    RoleNotFoundError,
)
from infrastructure.user.sqlalchemy.user_model import UserModel
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestUserSqlalchemyRepository:
    def test_add_user_persists_in_db(self, make_user, tst_db_session, seed_roles):
        session = tst_db_session
        user = make_user(roles={"cliente"})
        repo = userRepository(session=session)

        repo.add_user(user=user)

        row = session.query(UserModel).filter(UserModel.id == user.id).one()
        assert row.id == user.id
        assert row.name == user.name
        assert row.email == user.email
        assert row.hashed_password == user.hashed_password
        assert row.is_active == user.is_active

        # novo: garante que role foi associada (relationship roles no model)
        assert {r.name for r in (row.roles or [])} == {"cliente"}

    def test_find_user_by_id_returns_domain_entity(self, make_user, tst_db_session):
        session = tst_db_session
        user = make_user()

        # aqui inserimos direto o UserModel sem roles
        session.add(
            UserModel(
                id=user.id,
                name=user.name,
                email=user.email,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
            )
        )
        session.commit()

        repo = userRepository(session=session)
        found = repo.find_user_by_id(user_id=user.id)

        assert found.id == user.id
        assert found.name == user.name
        assert found.email == user.email
        assert found.hashed_password == user.hashed_password
        assert found.is_active == user.is_active
        assert found.roles == set()  # novo: sem roles porque não associamos no model

    def test_find_user_by_id_raises_when_not_found(self, tst_db_session):
        session = tst_db_session
        repo = userRepository(session=session)

        with pytest.raises(UserNotFoundError):
            repo.find_user_by_id(user_id=uuid4())

    def test_list_users_returns_all_users(self, make_user, tst_db_session):
        session = tst_db_session

        user1 = make_user(email="user1@example.com")
        user2 = make_user(email="user2@example.com")

        # inserindo direto no banco sem roles
        session.add_all(
            [
                UserModel(
                    id=user1.id,
                    name=user1.name,
                    email=user1.email,
                    hashed_password=user1.hashed_password,
                    is_active=user1.is_active,
                ),
                UserModel(
                    id=user2.id,
                    name=user2.name,
                    email=user2.email,
                    hashed_password=user2.hashed_password,
                    is_active=user2.is_active,
                ),
            ]
        )
        session.commit()

        repo = userRepository(session=session)
        users = repo.list_users()

        assert len(users) == 2
        assert any(
            u.id == user1.id
            and u.name == user1.name
            and u.email == user1.email
            and u.is_active == user1.is_active
            and u.roles == set()
            for u in users
        )
        assert any(
            u.id == user2.id
            and u.name == user2.name
            and u.email == user2.email
            and u.is_active == user2.is_active
            and u.roles == set()
            for u in users
        )

    def test_update_user_modifies_db(self, make_user, tst_db_session):
        session = tst_db_session
        user = make_user()

        session.add(
            UserModel(
                id=user.id,
                name=user.name,
                email=user.email,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
            )
        )
        session.commit()

        repo = userRepository(session=session)

        user.name = "Updated Name"
        user.email = "updated@example.com"
        user.is_active = False
        user.hashed_password = "updated-hash"

        repo.update_user(user=user)

        row = session.query(UserModel).filter(UserModel.id == user.id).one()
        assert row.name == "Updated Name"
        assert row.email == "updated@example.com"
        assert row.is_active is False
        assert row.hashed_password == "updated-hash"

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

        # make_user por padrão tem roles=set() no conftest
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

    def test_remove_role_from_user_raises_when_user_not_found(self, tst_db_session, seed_roles):
        session = tst_db_session
        repo = userRepository(session=session)

        with pytest.raises(UserNotFoundError):
            repo.remove_role_from_user(user_id=uuid4(), role_name="cliente")
            

    def test_add_role_to_user_raises_when_role_not_found(
        self, make_user, tst_db_session, seed_roles
    ):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user(email="role-not-found@example.com", roles={"cliente"})
        repo.add_user(user=user)

        with pytest.raises(RoleNotFoundError, match="not found"):
            repo.add_role_to_user(user_id=user.id, role_name="role_que_nao_existe")

    def test_add_role_to_user_is_idempotent_when_role_already_assigned(
        self, make_user, tst_db_session, seed_roles
    ):
        session = tst_db_session
        repo = userRepository(session=session)

        user = make_user(email="role-idempotent@example.com", roles={"cliente"})
        repo.add_user(user=user)

        # adiciona a mesma role novamente (não deve duplicar e nem falhar)
        repo.add_role_to_user(user_id=user.id, role_name="cliente")

        row = session.query(UserModel).filter(UserModel.id == user.id).one()
        roles = [r.name for r in (row.roles or [])]
        assert roles.count("cliente") == 1
        