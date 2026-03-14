
# from tests.conftest import make_task
from uuid import uuid4
import pytest
# Cria uma tarefa padrao para os testes


class TestTask:
	# teste para construir a task
	def test_task_initialization(self,make_task):
		task_id = uuid4()
		user_id = uuid4()	
		task_title = "Task 1"
		task_description = "Description for Task 1"
		task_completed = False
		task = make_task(id=task_id, 
			  user_id= user_id ,
			  title=task_title, 
			  description=task_description, 
			  completed=task_completed)
		assert task.id == task_id
		assert task.title == task_title
		assert task.description == task_description
		assert task.completed == task_completed

	# Teste para validação do Id da task
	def test_task_id_validation(self,make_task):
		with pytest.raises(ValueError, match="ID must be a valid UUID."):
			make_task(id="invalid-uuid")
			
	# Teste para validação do Id do usuário da task
	def test_task_user_id_validation(self,make_task):
		with pytest.raises(ValueError, match="User ID must be a valid UUID."):
			make_task(user_id = "invalid-uuid")
			
		
	# Teste para validação do título da task
	def test_task_title_validation(self,make_task):
		with pytest.raises(ValueError, match="Title must be a string."):
			make_task(title = 4)
			
	# Teste para validação do título da task vazio
	def test_task_title_validation_empty(self,make_task):
		with pytest.raises(ValueError, match="Title is required"):
			make_task(title = "")
			
	def test_task_title_validation_blank(self,make_task):
		with pytest.raises(ValueError, match="Title is required"):
			make_task(title = "        ")
	
	# Teste para validação da descrição da task
	def test_task_description_validation(self,make_task):
		with pytest.raises(ValueError, match="Description must be a string."):
			make_task( description = 4)
			
	# Teste para validação da descrição da task vazia
	def test_task_description_validation_empty(self,make_task):
		with pytest.raises(ValueError, match="Description is required"):
			make_task( description = "")
		
	# Teste para validação da descrição da task vazia
	def test_task_description_validation_blank(self,make_task):
		with pytest.raises(ValueError, match="Description is required"):
			make_task( description = "        ")

	# Teste para validação do campo completed da task
	def test_task_completed_validation(self,make_task):
		with pytest.raises(ValueError, match="Completed must be a boolean."):
			make_task( completed = "not-a-boolean")

			
	# teste para validar metodo mark_as_completed
	def test_mark_as_completed(self,make_task):
		task = make_task()
		task.mark_as_completed()
		assert task.completed == True	
		
	# teste para validar o metodo __str__ da task
	def test_task_str(self,make_task):
		task = make_task()
		expected_str = f"Task(id={task.id}, user_id={task.user_id}, title='{task.title}', completed={task.completed})"
		assert str(task) == expected_str		


		
			

			