from unittest.mock import MagicMock
from uuid import UUID

from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.list_users.list_users_dto import ListUsersInputDTO
from usecases.user.list_users.list_users_usecase import ListUsersUseCase


class TestMockListUsersUseCase:
    def test_list_users_usecase(self, make_user):
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        name1 = "Fulano"
        name2 = "Beltrano"

        email1 = "fulano@example.com"
        email2 = "beltrano@example.com"

        mock_user_repository.list_users.return_value = [
            make_user(name=name1, email=email1, is_active=True, roles={"cliente"}),
            make_user(name=name2, email=email2, is_active=False, roles={"prestador"}),
        ]

        use_case = ListUsersUseCase(mock_user_repository)

        input_dto = ListUsersInputDTO()
        output = use_case.execute(input=input_dto)

        assert len(output.users) == 2
        assert {u.name for u in output.users} == {name1, name2}
        assert {str(u.email) for u in output.users} == {email1, email2}
        assert {u.is_active for u in output.users} == {True, False}

        # novo: roles no output
        assert all(isinstance(u.roles, list) for u in output.users)
        assert any(u.roles == ["cliente"] for u in output.users)
        assert any(u.roles == ["prestador"] for u in output.users)

        mock_user_repository.list_users.assert_called_once()
        assert mock_user_repository.list_users.call_count == 1

        assert isinstance(output.users, list)
        assert all(isinstance(u.name, str) for u in output.users)
        assert all(isinstance(u.id, UUID) for u in output.users)
        # EmailStr no DTO é um tipo do pydantic; validar como string funciona bem
        assert all(isinstance(str(u.email), str) for u in output.users)
        assert all(isinstance(u.is_active, bool) for u in output.users)

    def test_list_users_usecase_empty(self):
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_user_repository.list_users.return_value = []

        use_case = ListUsersUseCase(mock_user_repository)

        input_dto = ListUsersInputDTO()
        output = use_case.execute(input=input_dto)

        mock_user_repository.list_users.assert_called_once()
        assert mock_user_repository.list_users.call_count == 1
        assert output.users == []