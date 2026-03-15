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

        user1 = make_user(name=name1)
        user2 = make_user(name=name2)

        user_repo.add_user(user=user1)
        user_repo.add_user(user=user2)

        use_case = ListUsersUseCase(user_repo)
        input_dto = ListUsersInputDTO()

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert isinstance(output.users, list)
        assert len(output.users) == 2
        assert {u.name for u in output.users} == {name1, name2}
        assert all(isinstance(u.name, str) for u in output.users)
        assert all(isinstance(u.id, UUID) for u in output.users)

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