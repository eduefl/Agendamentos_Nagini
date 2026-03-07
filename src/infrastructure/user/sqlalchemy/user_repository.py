from uuid import UUID
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from domain.user.user_exceptions import UserNotFoundError
from sqlalchemy.orm.session import Session
from infrastructure.user.sqlalchemy.user_model import UserModel



class userRepository(userRepositoryInterface):

	def __init__(self, session):
		self.session = session

	def add_user(self, user) -> None:
		user_model = UserModel(id=user.id, name=user.name)
		self.session.add(user_model)
		self.session.commit()
		return None

	def find_user_by_id(self, user_id: UUID) -> User:		
		# user_in_db: UserModel = self.session.query(UserModel).get(user_id) # get is deprecated, use filter instead
		#user_in_db: UserModel = self.session.query(UserModel).filter(UserModel.id == user_id).first()
		user_in_db = self.session.get(UserModel, user_id)
		if not user_in_db:
			# raise Exception(f"User with id {user_id} not found")
			raise UserNotFoundError(user_id)
		user = User(id=user_in_db.id, name=user_in_db.name)
		return user

	def list_users(self) -> list[User]:
		users_in_db: list[UserModel] = self.session.query(UserModel).all()
		users = [User(id=user_in_db.id, name=user_in_db.name) for user_in_db in users_in_db]
		return users


	def update_user(self, user: User)->None:
		self.session.query(UserModel).filter(UserModel.id == user.id).update({"name": user.name})
		self.session.commit()

		return None
	
