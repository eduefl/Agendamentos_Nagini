from uuid import uuid4

import pytest

from domain.task.task_entity import Task
from domain.user.user_entity import User


@pytest.fixture
def make_user():
    def _make_user(**overrides):
        data = {
            "id": uuid4(),
            "name": "John Doe",
        }
        data.update(overrides)
        return User(**data)

    return _make_user


@pytest.fixture
def make_task():
    def _make_task(**overrides):
        data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "title": "Task 1",
            "description": "Description for Task",
            "completed": False,
        }
        data.update(overrides)
        return Task(**data)

    return _make_task