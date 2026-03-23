from datetime import datetime, timedelta

class TestUserWithTasks:
    def test_user_collect_tasks(self, make_task, make_user):
        user = make_user(roles={"cliente"}) 
        task1 = make_task(user_id=user.id, title="Task 1")
        task2 = make_task(user_id=user.id, title="Task 2")

        user.collect_tasks([task1, task2])

        assert len(user.tasks) == 2
        assert task1 in user.tasks
        assert task2 in user.tasks

        assert user.count_pending_tasks() == 2

        task1.mark_as_completed()

        assert user.count_pending_tasks() == 1

        s = str(user)
        assert f"User(id={user.id}" in s
        assert f"name='{user.name}'" in s
        assert f"email='{user.email}'" in s
        assert f"is_active={user.is_active}" in s

        # se o __str__ passar a incluir roles, esse check garante consistência
        if hasattr(user, "roles"):
            assert "roles" in s

    def test_user_is_inactive_by_default(self,make_user):
        user = make_user()
        assert user.is_active is False


    def test_user_activation_lifecycle(self, make_user):
        user = make_user()

        assert user.is_active is False
        assert user.activation_code is None
        assert user.activation_code_expires_at is None

        expires_at = datetime.now() + timedelta(minutes=15)
        user.set_activation_code("abc12345", expires_at)

        assert user.activation_code == "abc12345"
        assert user.activation_code_expires_at == expires_at

        user.activate()

        assert user.is_active is True
        assert user.activation_code is None
        assert user.activation_code_expires_at is None