import pytest
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.list_tasks_from_user.list_tasks_from_user_dto import (
    ListTasksFromUserInputDTO,
    ListTasksFromUserOutputDTO,
)
from usecases.task.list_tasks_from_user.list_tasks_from_user_usecase import ListTasksFromUserUseCase


class TestListTasksFromUserUseCaseIntegration:
    def test_list_tasks_from_user(self, tst_db_session, make_user, make_task):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user_id = uuid4()
        user = make_user(id=user_id, name="John Doe")
        user_repo.add_user(user=user)

        task1 = make_task(user_id=user_id, title="Task 1", description="Description for Task 1")
        task2 = make_task(user_id=user_id, title="Task 2", description="Description for Task 2")
        task_repo.create_task(task=task1)
        task_repo.create_task(task=task2)

        use_case = ListTasksFromUserUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = ListTasksFromUserInputDTO(user_id=user_id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert isinstance(output, ListTasksFromUserOutputDTO)
        assert isinstance(output.tasks, list)
        assert len(output.tasks) == 2
        assert {t.title for t in output.tasks} == {"Task 1", "Task 2"}
        assert all(t.user_id == user_id for t in output.tasks)
        assert all(isinstance(t.title, str) for t in output.tasks)
        assert all(isinstance(t.description, str) for t in output.tasks)

    def test_list_tasks_from_user_empty(self, tst_db_session, make_user):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user_id = uuid4()
        user = make_user(id=user_id, name="John Doe")
        user_repo.add_user(user=user)

        use_case = ListTasksFromUserUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = ListTasksFromUserInputDTO(user_id=user_id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert isinstance(output, ListTasksFromUserOutputDTO)
        assert output.tasks == []

    def test_list_tasks_from_user_user_not_found(self, tst_db_session):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        use_case = ListTasksFromUserUseCase(task_repository=task_repo, user_repository=user_repo)

        missing_user_id = uuid4()
        input_dto = ListTasksFromUserInputDTO(user_id=missing_user_id)

        # Act / Assert
        with pytest.raises(UserNotFoundError) as exc_info:
            use_case.execute(input=input_dto)

        assert str(exc_info.value) == f"User with id {missing_user_id} not found"