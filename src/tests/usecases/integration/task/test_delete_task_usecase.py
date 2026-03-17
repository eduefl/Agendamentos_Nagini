import pytest
from uuid import uuid4

from domain.task.task_exceptions import TaskNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.delete_task.delete_task_dto import DeleteTaskInputDTO, DeleteTaskOutputDTO
from usecases.task.delete_task.delete_task_usecase import DeleteTaskUseCase


class TestDeleteTaskUseCaseIntegration:
    def test_delete_task(self, tst_db_session, make_user, make_task):
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

        usecase = DeleteTaskUseCase(task_repository=task_repo)
        input_dto = DeleteTaskInputDTO(id=task.id)

        # Act
        output = usecase.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, DeleteTaskOutputDTO)
        assert output.message == f"Task with id {task.id} deleted successfully."

        # Assert (persistência)
        with pytest.raises(TaskNotFoundError):
            task_repo.get_task_by_id(task_id=task.id)

    def test_delete_nonexistent_task(self, tst_db_session):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)

        usecase = DeleteTaskUseCase(task_repository=task_repo)

        missing_task_id = uuid4()
        input_dto = DeleteTaskInputDTO(id=missing_task_id)

        # Act / Assert
        with pytest.raises(TaskNotFoundError) as exc_info:
            usecase.execute(input=input_dto)

        assert str(exc_info.value) == f"Task with id {missing_task_id} not found"