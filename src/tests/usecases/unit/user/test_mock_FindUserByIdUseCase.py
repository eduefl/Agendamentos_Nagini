from unittest.mock import MagicMock
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from domain.task.task_entity import Task
from domain.user.user_entity import User
from domain.task.task_repository_interface import taskRepositoryInterface
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase
import pytest

class TestFindUserByIdUseCase:
    def test_find_user_by_id(self):
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        user_id = uuid4()
        mock_user_repository.find_user_by_id.return_value = User(id=user_id, name="John Doe")

        use_case = FindUserByIdUseCase(mock_user_repository, mock_task_repository)

        input_dto = findUserByIdInputDTO(id=user_id)
        output = use_case.execute(input=input_dto)

        assert output.id == user_id
        assert output.name == "John Doe"
        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        
    def test_find_user_by_id_returns_user_with_tasks(self):
        # Arrange
        user_id = uuid4()

        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        # O use case precisa de um User real (senão Pydantic reclama)
        user = User(id=user_id, name="John Doe")
        mock_user_repository.find_user_by_id.return_value = user

        # Para cobrir:
        # tasks_from_user = task_repository.list_tasks_from_user(...)
        # user.collect_tasks(tasks=tasks_from_user)
        task1 = Task( id = uuid4(), user_id=user_id, title="T1", description="D1", completed=False)
        task2 = Task(id = uuid4(), user_id=user_id, title="T2", description="D2", completed=True)
        mock_task_repository.list_tasks_from_user.return_value = [task1, task2]

        use_case = FindUserByIdUseCase(mock_user_repository, mock_task_repository)
        input_dto = findUserByIdInputDTO(id=user_id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert: garante que a linha do repo de tasks foi executada corretamente
        mock_task_repository.list_tasks_from_user.assert_called_once_with(user_id=user_id)

        # Assert: valida efeito do collect_tasks (tasks entraram e foram mapeadas pro DTO)
        assert output.id == user_id
        assert output.name == "John Doe"
        assert len(output.tasks) == 2
        assert {t.id for t in output.tasks} == {task1.id, task2.id}
        assert output.pending_tasks == 1  # só task1 está pendente		
        
    def test_find_user_by_id_raises_when_user_not_found(self):
        # Arrange
        user_id = uuid4()
        mock_user_repository = MagicMock(spec=userRepositoryInterface)
        mock_task_repository = MagicMock(spec=taskRepositoryInterface)

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

        use_case = FindUserByIdUseCase(mock_user_repository, mock_task_repository)
        input_dto = findUserByIdInputDTO(id=user_id)

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_task_repository.list_tasks_from_user.assert_not_called()
        		