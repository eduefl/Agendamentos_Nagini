from infrastructure.api.database import Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID


class UserModel(Base):

	__tablename__ = "tb_users"

	id = Column(UUID, primary_key=True, index=True)
	name = Column(String, index=True)
	# email = Column(String, unique=True, index=True)
	# hashed_password = Column(String)
	# is_active = Column(Boolean, default=True)
