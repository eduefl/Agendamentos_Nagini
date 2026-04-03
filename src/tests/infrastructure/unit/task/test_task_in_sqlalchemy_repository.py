from uuid import uuid4

import pytest

from domain.task.task_exceptions import TaskNotFoundError
from infrastructure.task.sqlalchemy.task_model import TaskModel
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository


class TestTaskSqlalchemyRepository:
    @staticmethod
    def _create_persisted_user(session, make_user):
        repo = userRepository(session=session)
        user = make_user(
            id=uuid4(),
            name=f"User {uuid4()}",
            email=f"{uuid4()}@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        repo.add_user(user)
        return user

    def test_register_task_persists_in_db(
        self,
        make_task,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)
        user = self._create_persisted_user(session, make_user)

        task = make_task(user_id=user.id)

        repo.create_task(task=task)

        row = session.query(TaskModel).filter(TaskModel.id == task.id).one()
        assert row.id == task.id
        assert row.user_id == task.user_id
        assert row.title == task.title
        assert row.description == task.description
        assert row.completed == task.completed

    def test_get_task_by_id_returns_domain_entity(
        self,
        make_task,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)
        user = self._create_persisted_user(session, make_user)

        task = make_task(user_id=user.id)

        repo.create_task(task=task)
        found = repo.get_task_by_id(task_id=task.id)

        assert found.id == task.id
        assert found.user_id == task.user_id
        assert found.title == task.title
        assert found.description == task.description
        assert found.completed == task.completed

    def test_get_task_by_id_raises_when_not_found(self, tst_db_session):
        session = tst_db_session
        repo = taskRepository(session=session)

        with pytest.raises(TaskNotFoundError):
            repo.get_task_by_id(task_id=uuid4())

    def test_update_task_modifies_db_record(
        self,
        make_task,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)
        user = self._create_persisted_user(session, make_user)

        task = make_task(user_id=user.id)
        repo.create_task(task=task)

        task.title = "Updated Title"
        task.description = "Updated Description"
        task.completed = True

        repo.update_task(task=task)

        row = session.query(TaskModel).filter(TaskModel.id == task.id).one()
        assert row.title == "Updated Title"
        assert row.description == "Updated Description"
        assert row.completed is True

    def test_update_task_raises_when_not_found(
        self,
        make_task,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)
        user = self._create_persisted_user(session, make_user)

        task = make_task(user_id=user.id)

        with pytest.raises(TaskNotFoundError):
            repo.update_task(task=task)

    def test_delete_task_removes_db_record(
        self,
        make_task,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)
        user = self._create_persisted_user(session, make_user)

        task = make_task(user_id=user.id)
        repo.create_task(task=task)

        row = session.query(TaskModel).filter(TaskModel.id == task.id).first()
        assert row is not None

        repo.delete_task(task_id=task.id)

        row = session.query(TaskModel).filter(TaskModel.id == task.id).first()
        assert row is None

    def test_delete_task_raises_when_not_found(self, tst_db_session):
        session = tst_db_session
        repo = taskRepository(session=session)

        with pytest.raises(TaskNotFoundError):
            repo.delete_task(task_id=uuid4())

    def test_list_tasks_from_user(
        self,
        make_task,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)

        owner = self._create_persisted_user(session, make_user)
        other_user = self._create_persisted_user(session, make_user)

        task1 = make_task(user_id=owner.id)
        task2 = make_task(user_id=owner.id)
        task3 = make_task(user_id=owner.id)
        task4 = make_task(user_id=other_user.id)

        repo.create_task(task=task1)
        repo.create_task(task=task2)
        repo.create_task(task=task3)
        repo.create_task(task=task4)

        tasks = repo.list_tasks_from_user(user_id=owner.id)

        assert len(tasks) == 3
        assert any(t.id == task1.id for t in tasks)
        assert any(t.id == task2.id for t in tasks)
        assert any(t.id == task3.id for t in tasks)
        assert all(t.id != task4.id for t in tasks)

    def test_list_tasks_from_user_returns_empty_list_when_no_tasks(
        self,
        make_user,
        tst_db_session,
        seed_roles,
    ):
        session = tst_db_session
        repo = taskRepository(session=session)
        user = self._create_persisted_user(session, make_user)

        tasks = repo.list_tasks_from_user(user_id=user.id)

        assert tasks == []