from uuid import uuid4
# from tests.conftest import make_user
import pytest



class TestUser:
	# teste para construir o usuario	
	def test_user_initialization(self,make_user):
		user_id = uuid4()
		user_name = "John Doe"
		user = make_user(id=user_id, name=user_name)
		assert user.id == user_id
		assert user.name == user_name
		assert user.tasks == []
		

	# Teste para valiacao do Id do usuario
	def test_user_id_validation(self,make_user):
		with pytest.raises(ValueError, match="ID must be a valid UUID."):
			make_user(id = "invalid-uuid")


	# Teste para valiacao do Id do usuario
	def test_user_name_validation(self,make_user):
		with pytest.raises(ValueError, match="Name must be a string."):
			make_user(name = 4)

	# Teste para valiacao do Id do usuario
	def test_user_name_validation_empty(self,make_user):
		with pytest.raises(ValueError, match="Name cannot be empty."):
			make_user(name = "")

	def test_user_name_validation_blank(self,make_user):
		with pytest.raises(ValueError, match="Name cannot be empty."):
			make_user(name = "       ")


