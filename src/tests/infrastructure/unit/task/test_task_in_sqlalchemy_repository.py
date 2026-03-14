from uuid import uuid4
from domain.task.task_exceptions import TaskNotFoundError
import pytest

from infrastructure.task.sqlalchemy.task_repository import taskRepository

from infrastructure.task.sqlalchemy.task_model import TaskModel


class TestTaskSqlalchemyRepository:
	def test_register_task_persists_in_db(self, make_task, tst_db_session):
		session = tst_db_session
		task = make_task()
		repo = taskRepository(session=session)

		repo.create_task(task=task)

		row = session.query(TaskModel).filter(TaskModel.id == task.id).one()
		assert row.id == task.id
		assert row.user_id == task.user_id
		assert row.title == task.title
		assert row.description == task.description
		assert row.completed == task.completed	

	def test_get_task_by_id_returns_domain_entity(self, make_task, tst_db_session):
		session = tst_db_session
		task = make_task()
		repo = taskRepository(session=session)
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

	def test_update_task_modifies_db_record(self, make_task, tst_db_session):
		session = tst_db_session
		task = make_task()
		repo = taskRepository(session=session)
		repo.create_task(task=task)

		task.title = "Updated Title"
		task.description = "Updated Description"
		task.completed = True
		repo.update_task(task=task)

		row = session.query(TaskModel).filter(TaskModel.id == task.id).one()
		assert row.title == "Updated Title"
		assert row.description == "Updated Description"
		assert row.completed is True # igual a =True 

	def test_update_task_raises_when_not_found(self, make_task, tst_db_session):
		session = tst_db_session
		repo = taskRepository(session=session)
		task = make_task()#construo a task mas não salvo no banco, ou seja ela não existe lá
		with pytest.raises(TaskNotFoundError):
			repo.update_task(task=task)# tento atualizar uma task que não existe no banco, 
										#ou seja, que não tem um registro correspondente, #
										# e espero que isso levante a exceção TaskNotFoundError

	def test_delete_task_removes_db_record(self, make_task, tst_db_session):
		session = tst_db_session
		task = make_task()
		repo = taskRepository(session=session)
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


	def test_list_tasks_from_user(self, make_task, tst_db_session):
		session = tst_db_session
		repo = taskRepository(session=session)
		user_id = uuid4()# Defino o usuario que vai ser dono das tasks vamos chamar de beltrao
		task1 = make_task(user_id = user_id) #crio 3 tasks para o beltrao
		task2 = make_task(user_id = user_id)
		task3 = make_task(user_id = user_id)
		task4 = make_task() #crio uma task para outro usuario, vamos chamar de fulano
		repo.create_task(task = task1)
		repo.create_task(task =task2)
		repo.create_task(task =task3)
		repo.create_task(task =task4)
		tasks = repo.list_tasks_from_user(user_id=user_id)# pego as tasks do beltrao
		assert len(tasks) == 3 # verifico se tem as 3 tasks do beltrao
		assert any(t.id == task1.id for t in tasks)
		assert any(t.id == task2.id for t in tasks)
		assert any(t.id == task3.id for t in tasks)
		assert all(t.id != task4.id for t in tasks) # verifico se a task do fulano não ta na lista do beltrao

	def test_list_tasks_from_user_returns_empty_list_when_no_tasks(self, tst_db_session):
		session = tst_db_session
		repo = taskRepository(session=session)
		user_id = uuid4()
		tasks = repo.list_tasks_from_user(user_id=user_id)
		assert tasks == []

		

			
