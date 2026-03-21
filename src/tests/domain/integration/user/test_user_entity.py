class TestUserWithTasks:
    # Teste para Adicionar Tarefas ao usuario
    def test_user_collect_tasks(self, make_task, make_user):
        user = make_user()
        task1 = make_task(user_id=user.id, title="Task 1")
        task2 = make_task(user_id=user.id, title="Task 2")

        user.collect_tasks([task1, task2])

        assert len(user.tasks) == 2
        assert task1 in user.tasks
        assert task2 in user.tasks

        assert user.count_pending_tasks() == 2

        task1.mark_as_completed()

        assert user.count_pending_tasks() == 1

        assert str(user) == (
            f"User(id={user.id}, name='{user.name}', email='{user.email}', is_active={user.is_active})"
        )