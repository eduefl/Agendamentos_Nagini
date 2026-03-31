from unittest.mock import MagicMock
from uuid import uuid4
from domain.user.user_exceptions import UserNotFoundError
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.task.list_tasks_from_user.list_tasks_from_user_dto import (
    ListTasksFromUserInputDTO,
    ListTasksFromUserOutputDTO,
)
from usecases.task.list_tasks_from_user.list_tasks_from_user_usecase import (
    ListTasksFromUserUseCase,
)
import pytest


class TestMockListTasksFromUserUseCase:
    def test_mock_list_tasks_from_user_usecase(self, make_task, make_user):

        # repositorio
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        user_id = uuid4()

        mock_user_repository.find_user_by_id.return_value = make_user(id=user_id)
        mock_task_repository.list_tasks_from_user.return_value = [
            make_task(
                user_id=user_id, title="Task 1", description="Description for Task 1"
            ),
            make_task(
                user_id=user_id, title="Task 2", description="Description for Task 2"
            ),
        ]

        # caso de uso
        use_case = ListTasksFromUserUseCase(
            task_repository=mock_task_repository, user_repository=mock_user_repository
        )
        input_dto = ListTasksFromUserInputDTO(user_id=user_id)
        output = use_case.execute(input=input_dto)

        # verificações
        assert isinstance(output, ListTasksFromUserOutputDTO)
        assert len(output.tasks) == 2
        assert {t.title for t in output.tasks} == {"Task 1", "Task 2"}
        assert isinstance(output.tasks, list)
        assert all(isinstance(t.title, str) for t in output.tasks)
        assert all(isinstance(t.description, str) for t in output.tasks)
        assert all(t.user_id == user_id for t in output.tasks)
        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_called_once_with(
            user_id=user_id
        )

    def test_mock_list_tasks_from_user_usecase_empty(self, make_user):
        # repositorio
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        user_id = uuid4()

        mock_user_repository.find_user_by_id.return_value = make_user(id=user_id)
        mock_task_repository.list_tasks_from_user.return_value = []

        # caso de uso
        use_case = ListTasksFromUserUseCase(
            task_repository=mock_task_repository, user_repository=mock_user_repository
        )
        input_dto = ListTasksFromUserInputDTO(user_id=user_id)
        output = use_case.execute(input=input_dto)

        # verificações
        assert isinstance(output, ListTasksFromUserOutputDTO)
        assert output.tasks == []
        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_called_once_with(
            user_id=user_id
        )

    def test_mock_list_tasks_from_user_usecase_user_not_found(self):
        # repositorio
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        user_id = uuid4()

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

        # caso de uso
        use_case = ListTasksFromUserUseCase(
            task_repository=mock_task_repository, user_repository=mock_user_repository
        )
        input_dto = ListTasksFromUserInputDTO(user_id=user_id)

        with pytest.raises(UserNotFoundError) as exc_info:
            use_case.execute(input=input_dto)

        assert str(exc_info.value) == f"User with id {user_id} not found"
        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_not_called()
