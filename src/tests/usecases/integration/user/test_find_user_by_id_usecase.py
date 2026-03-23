import pytest
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase


class TestFindUserByIdUseCaseIntegration:
    def test_find_user_by_id(self, tst_db_session, make_user, seed_roles):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)
        task_repo = taskRepository(session=session)

        user = make_user(
            name="John Doe",
            email="john.doe@example.com",
            is_active=True,
            roles={"cliente"},
        )
        user_repo.add_user(user=user)

        use_case = FindUserByIdUseCase(user_repo, task_repo)
        input_dto = findUserByIdInputDTO(id=user.id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.id == user.id
        assert output.name == "John Doe"
        assert str(output.email) == "john.doe@example.com"
        assert output.is_active is True
        assert output.tasks == []
        assert output.pending_tasks == 0
        assert output.roles == ["cliente"]

    def test_find_user_by_id_returns_user_with_tasks(
        self, tst_db_session, make_user, make_task, seed_roles
    ):
        session = tst_db_session
        user_repo = userRepository(session=session)
        task_repo = taskRepository(session=session)

        user = make_user(
            name="John Doe",
            email="john.doe@example.com",
            is_active=True,
            roles={"cliente"},
        )
        user_repo.add_user(user=user)

        task1 = make_task(user_id=user.id, title="T1", description="D1")
        task2 = make_task(user_id=user.id, title="T2", description="D2")
        task2.mark_as_completed()

        task_repo.create_task(task=task1)
        task_repo.create_task(task=task2)

        use_case = FindUserByIdUseCase(user_repo, task_repo)
        input_dto = findUserByIdInputDTO(id=user.id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.id == user.id
        assert output.name == "John Doe"
        assert str(output.email) == "john.doe@example.com"
        assert output.is_active is True
        assert output.roles == ["cliente"]

        assert len(output.tasks) == 2
        assert {t.id for t in output.tasks} == {task1.id, task2.id}
        assert output.pending_tasks == 1  # task1 pendente, task2 concluída

    def test_find_user_by_id_raises_when_user_not_found(self, tst_db_session):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)
        task_repo = taskRepository(session=session)

        use_case = FindUserByIdUseCase(user_repo, task_repo)
        input_dto = findUserByIdInputDTO(id=uuid4())

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)

    def test_find_user_by_id_returns_inactive_user(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)
        task_repo = taskRepository(session=session)

        user = make_user(
            name="John Doe",
            email="john.doe@example.com",
            is_active=False,
            roles={"cliente"},
        )
        user_repo.add_user(user=user)

        use_case = FindUserByIdUseCase(user_repo, task_repo)
        input_dto = findUserByIdInputDTO(id=user.id)

        output = use_case.execute(input=input_dto)

        assert output.id == user.id
        assert output.is_active is False
        assert output.roles == ["cliente"]