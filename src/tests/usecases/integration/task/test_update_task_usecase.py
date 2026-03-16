import pytest
from uuid import uuid4

from domain.task.task_exceptions import TaskNotFoundError
from domain.user.user_exceptions import UserNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.update_task.update_task_dto import UpdateTaskInputDTO, UpdateTaskOutputDTO
from usecases.task.update_task.update_task_usecase import UpdateTaskUseCase


class TestUpdateTaskUseCaseIntegration:
    def test_update_task_usecase(self, tst_db_session, make_user, make_task):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        original_user = make_user(name="John Doe")
        new_user = make_user(name="Jane Doe")
        user_repo.add_user(user=original_user)
        user_repo.add_user(user=new_user)

        task = make_task(
            user_id=original_user.id,
            title="Task 1",
            description="Description for Task",
            completed=False,
        )
        task_repo.create_task(task=task)

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = UpdateTaskInputDTO(
            id=task.id,
            user_id=new_user.id,
            title="Updated Task 1",
            description="Updated Description for Task",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, UpdateTaskOutputDTO)
        assert output.id == task.id
        assert output.user_id == new_user.id
        assert output.title == "Updated Task 1"
        assert output.description == "Updated Description for Task"
        assert output.completed is False

        # Assert (persistência)
        updated_task = task_repo.get_task_by_id(task_id=task.id)
        assert updated_task.id == task.id
        assert updated_task.user_id == new_user.id
        assert updated_task.title == "Updated Task 1"
        assert updated_task.description == "Updated Description for Task"
        assert updated_task.completed is False

    def test_update_task_usecase_task_not_found(self, tst_db_session, make_user):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user = make_user(name="John Doe")
        user_repo.add_user(user=user)

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)

        missing_task_id = uuid4()
        input_dto = UpdateTaskInputDTO(
            id=missing_task_id,
            user_id=user.id,
            title="Updated Task 1",
            description="Updated Description for Task",
        )

        # Act / Assert
        with pytest.raises(TaskNotFoundError) as exc_info:
            use_case.execute(input=input_dto)

        assert str(exc_info.value) == f"Task with id {missing_task_id} not found"

    def test_update_task_usecase_user_not_found(self, tst_db_session, make_user, make_task):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        existing_user = make_user(name="John Doe")
        user_repo.add_user(user=existing_user)

        task = make_task(
            user_id=existing_user.id,
            title="Task 1",
            description="Description for Task",
            completed=False,
        )
        task_repo.create_task(task=task)

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)

        missing_user_id = uuid4()
        input_dto = UpdateTaskInputDTO(
            id=task.id,
            user_id=missing_user_id,
            title="Updated Task 1",
            description="Updated Description for Task",
        )

        # Act / Assert
        with pytest.raises(UserNotFoundError) as exc_info:
            use_case.execute(input=input_dto)

        assert str(exc_info.value) == f"User with id {missing_user_id} not found"

    def test_update_task_usecase_partial_update_title_only(self, tst_db_session, make_user, make_task):
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

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = UpdateTaskInputDTO(
            id=task.id,
            title="Partially Updated Task 1",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert (output)
        assert isinstance(output, UpdateTaskOutputDTO)
        assert output.id == task.id
        assert output.user_id == user.id
        assert output.title == "Partially Updated Task 1"
        assert output.description == "Description for Task"
        assert output.completed is False

        # Assert (persistência)
        updated_task = task_repo.get_task_by_id(task_id=task.id)
        assert updated_task.user_id == user.id
        assert updated_task.title == "Partially Updated Task 1"
        assert updated_task.description == "Description for Task"
        assert updated_task.completed is False

    def test_update_task_usecase_partial_update_not_title(self, tst_db_session, make_user, make_task):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user = make_user(name="John Doe")
        new_user = make_user(name="Jane Doe")
        user_repo.add_user(user=user)
        user_repo.add_user(user=new_user)

        task = make_task(
            user_id=user.id,
            title="Task 1",
            description="Description for Task",
            completed=False,
        )
        task_repo.create_task(task=task)

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = UpdateTaskInputDTO(
            id=task.id,
            user_id=new_user.id,
            description="Updated Description for Task not updated title",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.title == "Task 1"
        assert output.user_id == new_user.id
        assert output.description == "Updated Description for Task not updated title"

        updated_task = task_repo.get_task_by_id(task_id=task.id)
        assert updated_task.title == "Task 1"
        assert updated_task.user_id == new_user.id
        assert updated_task.description == "Updated Description for Task not updated title"
        assert updated_task.completed is False

    def test_update_task_usecase_partial_update_not_description(self, tst_db_session, make_user, make_task):
        # Arrange
        session = tst_db_session
        task_repo = taskRepository(session=session)
        user_repo = userRepository(session=session)

        user = make_user(name="John Doe")
        new_user = make_user(name="Jane Doe")
        user_repo.add_user(user=user)
        user_repo.add_user(user=new_user)

        task = make_task(
            user_id=user.id,
            title="Task 1",
            description="Description for Task",
            completed=False,
        )
        task_repo.create_task(task=task)

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = UpdateTaskInputDTO(
            id=task.id,
            user_id=new_user.id,
            title="Updated Task 1",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.title == "Updated Task 1"
        assert output.user_id == new_user.id
        assert output.description == "Description for Task"

        updated_task = task_repo.get_task_by_id(task_id=task.id)
        assert updated_task.title == "Updated Task 1"
        assert updated_task.user_id == new_user.id
        assert updated_task.description == "Description for Task"
        assert updated_task.completed is False

    def test_update_task_usecase_partial_update_not_user(self, tst_db_session, make_user, make_task):
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

        use_case = UpdateTaskUseCase(task_repository=task_repo, user_repository=user_repo)
        input_dto = UpdateTaskInputDTO(
            id=task.id,
            title="Updated Task 1",
            description="Updated Description for Task not updated user",
        )

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.user_id == user.id
        assert output.title == "Updated Task 1"
        assert output.description == "Updated Description for Task not updated user"

        updated_task = task_repo.get_task_by_id(task_id=task.id)
        assert updated_task.user_id == user.id
        assert updated_task.title == "Updated Task 1"
        assert updated_task.description == "Updated Description for Task not updated user"
        assert updated_task.completed is False