import pytest
from uuid import uuid4

from domain.user.user_exceptions import EmailAlreadyExistsError, UserNotFoundError
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.update_user.update_user_dto import UpdateUserInputDTO
from usecases.user.update_user.update_user_usecase import updateUserUsecase


class TestUpdateUserUseCaseIntegration:
    def test_update_user_usecase(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=True,
            roles={"cliente"},
        )
        user_repo.add_user(user=user)

        use_case = updateUserUsecase(user_repo)
        input_dto = UpdateUserInputDTO(
            id=user.id,
            name="Jane Doe",
            email="jane@example.com",
            is_active=False,
        )

        output = use_case.execute(input_dto)

        assert output.id == user.id
        assert output.name == "Jane Doe"
        assert str(output.email) == "jane@example.com"
        assert output.is_active is False

        # se o DTO de saída tiver roles, valida também (update não deve mexer nisso)
        if hasattr(output, "roles"):
            assert output.roles == ["cliente"]

        updated_user = user_repo.find_user_by_id(user_id=user.id)
        assert updated_user.name == "Jane Doe"
        assert updated_user.email == "jane@example.com"
        assert updated_user.is_active is False
        assert updated_user.roles == {"cliente"}

    def test_update_user_usecase_user_not_found(self, tst_db_session):
        session = tst_db_session
        user_repo = userRepository(session=session)

        use_case = updateUserUsecase(user_repo)
        input_dto = UpdateUserInputDTO(
            id=uuid4(),
            name="Jane Doe",
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

    def test_update_user_usecase_raises_email_already_exists(
        self, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        user_repo = userRepository(session=session)

        # cria 2 usuários com emails distintos
        user1 = make_user(
            name="User 1", email="user1@example.com", is_active=True, roles={"cliente"}
        )
        user2 = make_user(
            name="User 2", email="user2@example.com", is_active=True, roles={"prestador"}
        )
        user_repo.add_user(user=user1)
        user_repo.add_user(user=user2)

        use_case = updateUserUsecase(user_repo)

        # tenta colocar no user1 o email do user2 (violando unique)
        input_dto = UpdateUserInputDTO(
            id=user1.id,
            email="user2@example.com",
        )

        with pytest.raises(EmailAlreadyExistsError, match="user2@example.com"):
            use_case.execute(input_dto)

        # garante que não alterou o user1
        user1_db = user_repo.find_user_by_id(user_id=user1.id)
        assert user1_db.email == "user1@example.com"
        assert user1_db.name == "User 1"
        assert user1_db.is_active is True
        assert user1_db.roles == {"cliente"}