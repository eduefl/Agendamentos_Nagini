from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.task.task_entity import Task
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.user.user_entity import User
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase


class TestFindUserByIdUseCase:
    def test_find_user_by_id(self):
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        user_id = uuid4()

        mock_user_repository.find_user_by_id.return_value = User(
            id=user_id,
            name="John Doe",
            email="john@example.com",
            hashed_password="hashed",
            is_active=True,
            roles={"cliente"},
        )

        # se o use case chamar list_tasks_from_user e você não setar retorno,
        # o mock retorna outro MagicMock; melhor fixar como lista vazia
        mock_task_repository.list_tasks_from_user.return_value = []

        use_case = FindUserByIdUseCase(mock_user_repository, mock_task_repository)

        input_dto = findUserByIdInputDTO(id=user_id)
        output = use_case.execute(input=input_dto)

        assert output.id == user_id
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is True
        assert output.tasks == []
        assert output.pending_tasks == 0
        assert output.roles == ["cliente"]

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_called_once_with(user_id=user_id)

    def test_find_user_by_id_returns_user_with_tasks(self):
        user_id = uuid4()

        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        user = User(
            id=user_id,
            name="John Doe",
            email="john@example.com",
            hashed_password="hashed",
            is_active=True,
            roles={"cliente"},
        )
        mock_user_repository.find_user_by_id.return_value = user

        task1 = Task(
            id=uuid4(),
            user_id=user_id,
            title="T1",
            description="D1",
            completed=False,
        )
        task2 = Task(
            id=uuid4(),
            user_id=user_id,
            title="T2",
            description="D2",
            completed=True,
        )
        mock_task_repository.list_tasks_from_user.return_value = [task1, task2]

        use_case = FindUserByIdUseCase(mock_user_repository, mock_task_repository)
        input_dto = findUserByIdInputDTO(id=user_id)

        output = use_case.execute(input=input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_called_once_with(user_id=user_id)

        assert output.id == user_id
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is True
        assert output.roles == ["cliente"]

        assert len(output.tasks) == 2
        assert {t.id for t in output.tasks} == {task1.id, task2.id}
        assert output.pending_tasks == 1  # só task1 está pendente

    def test_find_user_by_id_raises_when_user_not_found(self):
        user_id = uuid4()
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

        use_case = FindUserByIdUseCase(mock_user_repository, mock_task_repository)
        input_dto = findUserByIdInputDTO(id=user_id)

        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_not_called()