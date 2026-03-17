import pytest
from uuid import uuid4

from domain.task.task_exceptions import TaskNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.mark_as_completed.mark_as_completed_dto import (
    MarkAsCompletedInputDTO,
    MarkAsCompletedOutputDTO,
)
from usecases.task.mark_as_completed.mark_as_completed_usecase import MarkAsCompletedUseCase


class TestMarkAsCompletedUseCaseIntegration:
    def test_mark_as_completed(self, tst_db_session, make_user, make_task):
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

        usecase = MarkAsCompletedUseCase(task_repository=task_repo)
        input_dto = MarkAsCompletedInputDTO(id=task.id)

        # Act
        output = usecase.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, MarkAsCompletedOutputDTO)
        assert output.id == task.id
        assert output.user_id == user.id
        assert output.title == "Task 1"
        assert output.description == "Description for Task"
        assert output.completed is True

        # Assert (persistência)
        updated_task = task_repo.get_task_by_id(task_id=task.id)
        assert updated_task.id == task.id
        assert updated_task.user_id == user.id
        assert updated_task.title == "Task 1"
        assert updated_task.description == "Description for Task"
        assert updated_task.completed is True

    def test_mark_as_completed_nonexistent_task(self, tst_db_session):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)

        usecase = MarkAsCompletedUseCase(task_repository=task_repo)

        missing_task_id = uuid4()
        input_dto = MarkAsCompletedInputDTO(id=missing_task_id)

        # Act / Assert
        with pytest.raises(TaskNotFoundError) as exc_info:
            usecase.execute(input=input_dto)

        assert str(exc_info.value) == f"Task with id {missing_task_id} not found"

        