from uuid import uuid4
from domain.user.user_exceptions import UserNotFoundError
import pytest

from infrastructure.user.sqlalchemy.user_repository import userRepository
from infrastructure.user.sqlalchemy.user_model import UserModel  

class TestUserSqlalchemyRepository:
	def test_add_user_persists_in_db(self, make_user, tst_db_session):
		session = tst_db_session
		user = make_user()
		repo = userRepository(session=session)

		repo.add_user(user=user)

		# valida persistência consultando o model (não só "assert True")
		row = session.query(UserModel).filter(UserModel.id == user.id).one()
		assert row.id == user.id
		assert row.name == user.name
        


	def test_find_user_by_id_returns_domain_entity(self,make_user, tst_db_session):
		session = tst_db_session
		user = make_user()
		session.add(UserModel(id=user.id, name=user.name))
		session.commit()

		repo = userRepository(session=session)
		found = repo.find_user_by_id(user_id=user.id)

		assert found.id == user.id
		assert found.name == user.name


	def test_find_user_by_id_raises_when_not_found(self, tst_db_session):
		session = tst_db_session
		repo = userRepository(session=session)
		with pytest.raises(UserNotFoundError):
			repo.find_user_by_id(user_id=uuid4())
	
	def test_list_users_returns_all_users(self, make_user,tst_db_session):

		session = tst_db_session
		user1 = make_user()
		user2 = make_user()
		session.add_all([
			UserModel(id=user1.id, name=user1.name),
			UserModel(id=user2.id, name=user2.name)
		])
		session.commit()

		repo = userRepository(session=session)
		users = repo.list_users()

		assert len(users) == 2
		assert any(u.id == user1.id and u.name == user1.name for u in users)
		assert any(u.id == user2.id and u.name == user2.name for u in users)


	def test_update_user_modifies_db(self, make_user, tst_db_session):
		session = tst_db_session
		user = make_user()
		session.add(UserModel(id=user.id, name=user.name))
		session.commit()

		repo = userRepository(session=session)
		user.name = "Updated Name"
		repo.update_user(user=user)

		row = session.query(UserModel).filter(UserModel.id == user.id).one()
		assert row.name == "Updated Name"

	def test_update_user_raises_when_not_found(self, make_user, tst_db_session):

		session = tst_db_session
		repo = userRepository(session=session)
		user = make_user()  # cria um usuário mas não o adiciona ao banco
		with pytest.raises(UserNotFoundError):
			repo.update_user(user=user)
			