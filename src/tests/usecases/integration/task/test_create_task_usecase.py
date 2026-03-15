import pytest
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.create_task.create_task_dto import CreateTaskInputDTO, createTaskOutputDTO
from usecases.task.create_task.create_task_usecase import CreateTaskUseCase


class TestCreateTaskUseCaseIntegration:
    def test_create_task_valid(self, tst_db_session, make_user):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user = make_user(name="John Doe")
        user_repo.add_user(user=user)

        use_case = CreateTaskUseCase(task_repo, user_repo)

        input_dto = CreateTaskInputDTO(
            user_id=user.id,
            title="Task 1",
            description="Description for Task",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, createTaskOutputDTO)
        assert output.id is not None
        assert output.user_id == user.id
        assert output.title == "Task 1"
        assert output.description == "Description for Task"
        assert output.completed is False

        # Assert (persistência no banco)
        created_task = task_repo.get_task_by_id(task_id=output.id)
        assert created_task.id == output.id
        assert created_task.user_id == user.id
        assert created_task.title == "Task 1"
        assert created_task.description == "Description for Task"
        assert created_task.completed is False

    def test_create_task_user_not_found(self, tst_db_session):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        use_case = CreateTaskUseCase(task_repo, user_repo)

        input_dto = CreateTaskInputDTO(
            user_id=uuid4(),
            title="Task 1",
            description="Description for Task",
        )

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)