from uuid import UUID

from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.list_users.list_users_dto import ListUsersInputDTO
from usecases.user.list_users.list_users_usecase import ListUsersUseCase


class TestListUsersUseCaseIntegration:
    def test_list_users_usecase(self, tst_db_session, make_user):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)

        name1 = "Fulano"
        name2 = "Beltrano"

        email1 = "fulano@example.com"
        email2 = "beltrano@example.com"

        user1 = make_user(name=name1, email=email1, is_active=True)
        user2 = make_user(name=name2, email=email2, is_active=False)

        user_repo.add_user(user=user1)
        user_repo.add_user(user=user2)

        use_case = ListUsersUseCase(user_repo)
        input_dto = ListUsersInputDTO()

        # Act
        output = use_case.execute(input=input_dto)

        assert isinstance(output.users, list)
        assert len(output.users) == 2

        assert {u.name for u in output.users} == {name1, name2}
        assert {str(u.email) for u in output.users} == {email1, email2}
        assert {u.is_active for u in output.users} == {True, False}

        assert all(isinstance(u.name, str) for u in output.users)
        assert all(isinstance(u.id, UUID) for u in output.users)
        assert all(isinstance(str(u.email), str) for u in output.users)
        assert all(isinstance(u.is_active, bool) for u in output.users)

    def test_list_users_usecase_empty(self, tst_db_session):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)

        use_case = ListUsersUseCase(user_repo)
        input_dto = ListUsersInputDTO()

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.users == []