import pytest
from uuid import uuid4

from domain.task.task_exceptions import TaskNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.get_task_by_id.get_task_by_id_dto import (
    getTaskByIdInputDTO,
    getTaskByIdOutputDTO,
)
from usecases.task.get_task_by_id.get_task_by_id_usecase import GetTaskByIdUseCase


class TestGetTaskByIdUseCaseIntegration:
    def test_get_task_by_id_usecase(self, tst_db_session, make_user, make_task):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user = make_user(name="John Doe")
        user_repo.add_user(user=user)

        task = make_task(
            user_id=user.id,
            title="Task 1",
            description="Description for Task",
            completed=False,
        )
        task_repo.create_task(task=task)

        use_case = GetTaskByIdUseCase(task_repository=task_repo)
        input_dto = getTaskByIdInputDTO(id=task.id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert isinstance(output, getTaskByIdOutputDTO)
        assert output.id == task.id
        assert output.user_id == user.id
        assert output.title == "Task 1"
        assert output.description == "Description for Task"
        assert output.completed is False

    def test_get_task_by_id_usecase_task_not_found(self, tst_db_session):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)

        use_case = GetTaskByIdUseCase(task_repository=task_repo)
        missing_task_id = uuid4()
        input_dto = getTaskByIdInputDTO(id=missing_task_id)

        # Act / Assert
        with pytest.raises(TaskNotFoundError) as exc_info:
            use_case.execute(input=input_dto)

        assert str(exc_info.value) == f"Task with id {missing_task_id} not found"